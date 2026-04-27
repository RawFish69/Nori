"""AI and utility tool commands."""

import asyncio
import time

import hikari
import lightbulb
import python_weather
import requests

import lib.config as config
from lib.config import (
    AI_API_KEY,
    MODELS,
    BOT_OWNER_ID,
    GPT_LOG_CHANNEL_ID,
)
from lib.utils import check_user_access


def _split_long_message(text: str, chunk_size: int = 1500):
    return [text[index:index + chunk_size] for index in range(0, len(text), chunk_size)]


def _ensure_chat_state(user_name: str):
    if user_name not in config.user_chat_histories:
        config.user_chat_histories[user_name] = {"messages": [], "response_timestamps": []}
        config.bot_responses[user_name] = {"messages": [], "response_timestamps": []}


def gpt_response(user_name: str, prompt: str):
    cooldown = 30
    current_time = time.time()
    _ensure_chat_state(user_name)

    user_ts = config.user_chat_histories[user_name]["response_timestamps"]
    if len(user_ts) >= 3 and current_time - user_ts[-1] < cooldown:
        cd = cooldown - (current_time - user_ts[-1])
        return f"Please wait a moment before trying again, Cooldown: <t:{int(current_time + cd)}:R>"

    endpoint = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AI_API_KEY}",
    }
    payload = {
        "model": config.engine,
        "messages": [
            {"role": "system", "content": "You are Nori, RawFish's Assistant Bot"},
            {"role": "user", "content": f"Username: {user_name}, Prompt: {prompt}"},
            {
                "role": "assistant",
                "content": (
                    f"prompt history: {config.user_chat_histories[user_name]['messages']}, "
                    f"message history: {config.bot_responses[user_name]['messages']}"
                ),
            },
        ],
        "max_tokens": 3000,
        "top_p": 1,
    }

    response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
    result = response.json()
    generated_text = result.get("choices", [{}])[0].get("message", {}).get("content", "No response generated.")

    config.user_chat_histories[user_name]["messages"].append(prompt)
    config.user_chat_histories[user_name]["response_timestamps"].append(int(current_time))
    config.bot_responses[user_name]["messages"].append(generated_text)
    config.bot_responses[user_name]["response_timestamps"].append(int(current_time))
    return generated_text


def gpt_vision(user_name: str, prompt: str, image_url: str):
    cooldown = 20
    current_time = time.time()
    _ensure_chat_state(user_name)

    user_ts = config.user_chat_histories[user_name]["response_timestamps"]
    if len(user_ts) >= 3 and current_time - user_ts[-1] < cooldown:
        cd = cooldown - (current_time - user_ts[-1])
        return f"Please wait a moment before trying again, Cooldown: <t:{int(current_time + cd)}:R>"

    endpoint = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AI_API_KEY}",
    }
    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ],
        "max_tokens": 2000,
    }

    response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
    result = response.json()
    generated_text = result.get("choices", [{}])[0].get("message", {}).get("content", "No response generated.")

    config.user_chat_histories[user_name]["messages"].append(prompt)
    config.user_chat_histories[user_name]["response_timestamps"].append(int(current_time))
    config.bot_responses[user_name]["messages"].append(generated_text)
    config.bot_responses[user_name]["response_timestamps"].append(int(current_time))
    return generated_text


def load_ai_tools_commands(bot: lightbulb.BotApp, blocked_users: list = None):
    """Load AI command set."""

    @bot.command
    @lightbulb.option("keywords", "Keywords or arguments")
    @lightbulb.command("image", "AI generated image")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def generate_image(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        args = ctx.options.keywords
        text = str(args)
        await ctx.respond(f"Keywords: **{args}**")
        try:
            url = "https://api.openai.com/v1/images/generations"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {AI_API_KEY}",
            }
            payload = {
                "model": "image-alpha-001",
                "prompt": text,
                "num_images": 1,
                "size": "1024x1024",
                "response_format": "url",
            }
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            result = response.json()
            image_url = result.get("data", [{}])[0].get("url")
            if not image_url:
                await ctx.respond(f"Image generation failed: `{result}`")
                return
            await ctx.respond(image_url)
        except Exception as error:
            await ctx.respond(f"Image generation error: {error}")

    @bot.command
    @lightbulb.option("image", "Image URL", required=False)
    @lightbulb.option("prompt", "Prompt containing user input content")
    @lightbulb.command("ask", "Ask AI something")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def auto_reply(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        endpoint = "https://api.openai.com/v1/completions"
        prompt = ctx.options.prompt
        generated_text = ""

        user = await bot.rest.fetch_user(ctx.user.id)
        username = user.username
        await ctx.respond(f"Requested by {user}\nPrompt: {prompt}")

        if "gpt" in config.engine.lower():
            try:
                if not ctx.options.image:
                    generated_text = gpt_response(username, prompt)
                else:
                    generated_text = gpt_vision(username, prompt, ctx.options.image)

                if len(generated_text) > 1500:
                    split_messages = _split_long_message(generated_text, 1500)
                    total_parts = len(split_messages)
                    for index, message in enumerate(split_messages):
                        message_with_part = f"**[{index + 1}/{total_parts}]** {message}"
                        if index == 0:
                            await ctx.edit_last_response(message_with_part)
                        else:
                            await ctx.respond(message_with_part)
                        await asyncio.sleep(1)
                else:
                    await ctx.edit_last_response(generated_text)
            except Exception as error:
                print(f"GPT ERROR: {error}")
                generated_text = "Error occurred while handling user request."
                await ctx.edit_last_response(generated_text)
        else:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {AI_API_KEY}",
            }
            payload = {
                "model": config.engine,
                "prompt": prompt,
                "max_tokens": 2000,
                "temperature": 0.5,
                "top_p": 1,
            }
            response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
            result = response.json()
            generated_text = result.get("choices", [{}])[0].get("text", "No response generated.")

            if len(generated_text) > 1500:
                split_messages = _split_long_message(generated_text, 1500)
                total_parts = len(split_messages)
                for index, message in enumerate(split_messages):
                    message_with_part = f"[{index + 1}/{total_parts}] {message}"
                    if index == 0:
                        await ctx.edit_last_response(message_with_part)
                    else:
                        await ctx.respond(message_with_part)
                    await asyncio.sleep(1)
            else:
                await ctx.edit_last_response(generated_text)

        try:
            log_channel = GPT_LOG_CHANNEL_ID
            if generated_text:
                if len(generated_text) > 1500:
                    split_messages = _split_long_message(generated_text, 1500)
                    total_parts = len(split_messages)
                    for index, message in enumerate(split_messages):
                        msg = f"[{index + 1}/{total_parts}] `{message}`"
                        await bot.rest.create_message(channel=log_channel, content=msg)
                        await asyncio.sleep(1)
                else:
                    await bot.rest.create_message(channel=log_channel, content=f"<**AI-Reply**>: `{generated_text}`")
        except Exception as error:
            print(f"Unable to write AI log message: {error}")

    @bot.command
    @lightbulb.command("chat", "AI chat components")
    @lightbulb.implements(lightbulb.SlashCommandGroup)
    async def chat(ctx: lightbulb.Context):
        pass

    @chat.child()
    @lightbulb.option(name="user_id", description="Specific user (Owner only)", required=False, type=hikari.User)
    @lightbulb.command(name="history", description="Chat history")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def chat_prompts(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        if ctx.options.user_id and ctx.user.id == BOT_OWNER_ID:
            target_user = await bot.rest.fetch_user(ctx.options.user_id)
        elif ctx.options.user_id and ctx.user.id != BOT_OWNER_ID:
            await ctx.respond("You do not have permission.")
            return
        else:
            target_user = await bot.rest.fetch_user(ctx.user.id)

        user_name = target_user.username
        if user_name not in config.user_chat_histories:
            await ctx.respond(f"No chat history found for {user_name}")
            return

        prompt_history = config.user_chat_histories[user_name]["messages"]
        response_history = config.bot_responses[user_name]["messages"]
        total_prompts = len(prompt_history)
        for index, _section in enumerate(prompt_history):
            chat_history = (
                f"**Chat history [{index + 1}/{total_prompts}]**\n"
                f"{user_name}: `{prompt_history[index]}`\n"
                f"Bot response: `{response_history[index][:1000]}`"
            )
            if len(response_history[index]) > 1000:
                chat_history += "...\n__Response exceeding 1000 characters, full text in log__"
            await ctx.respond(chat_history)
            await asyncio.sleep(1)

    @chat.child()
    @lightbulb.option(name="user_id", description="Specific user (Owner only)", required=False, type=hikari.User)
    @lightbulb.command(name="clear", description="Clear chat history")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def chat_clear(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        if ctx.options.user_id and ctx.user.id == BOT_OWNER_ID:
            target_user = await bot.rest.fetch_user(ctx.options.user_id)
        elif ctx.options.user_id and ctx.user.id != BOT_OWNER_ID:
            await ctx.respond("You do not have permission.")
            return
        else:
            target_user = await bot.rest.fetch_user(ctx.user.id)

        user_name = target_user.username
        if user_name in config.user_chat_histories:
            del config.user_chat_histories[user_name]
            del config.bot_responses[user_name]
            await ctx.respond(f"Chat history cleared for `{user_name}`")
        else:
            await ctx.respond(f"No chat history found for {user_name}")

    @bot.command
    @lightbulb.command("model", "AI engine commands")
    @lightbulb.implements(lightbulb.SlashCommandGroup)
    async def model(ctx: lightbulb.Context):
        pass

    @model.child()
    @lightbulb.add_checks(lightbulb.owner_only)
    @lightbulb.option("model", "Select an AI-Text model", choices=MODELS[:7])
    @lightbulb.command("select", "Select an Model (Owner only)")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def change_engine(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        model_choice = ctx.options.model
        await ctx.respond(f"AI Model has switched to {model_choice}")
        config.engine = model_choice

    @model.child()
    @lightbulb.command("version", "Display current model")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def check_model_version(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        await ctx.respond(f"Currently running on `{config.engine}` AI model, contact RawFish for issues")

    @bot.command
    @lightbulb.option("location", "Name of the city")
    @lightbulb.command("weather", "Checks the weather status of a city")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def check_weather(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        city = ctx.options.location
        try:
            async with python_weather.Client() as client:
                weather = await client.get(city)
        except Exception as error:
            await ctx.respond(f"Weather request failed: {error}")
            return

        hourly_data = []
        the_dates = []
        forecast_data = []
        feels_like_c = weather.current.feels_like
        display_weather = f"```City/Area: {city}\n"
        display_weather += f"Region: {weather.nearest_area.region}, {weather.nearest_area.country}\n"
        display_weather += f"Current Temperature: {weather.current.temperature} C\n"
        display_weather += f"Feels like {feels_like_c} C\n"
        for forecast in weather.forecasts:
            the_dates.append(forecast.date)
            hourly_data.clear()
            for hourly in forecast.hourly:
                hourly_data.append(
                    f"[{hourly.time.hour}:{hourly.time.minute}{hourly.time.second}] {hourly.description}"
                )
            forecast_data.append(list(hourly_data))

        index = 1
        if the_dates:
            display_weather += f"{the_dates[0]} (Today):\n"
        if forecast_data:
            for section in forecast_data[0]:
                if index < 2:
                    display_weather += f"{section} -> "
                    index += 1
                else:
                    display_weather += f"{section}\n"
                    index = 1
        display_weather += (
            f"Wind Direction: {weather.current.wind_direction}, Wind Speed: {weather.current.wind_speed} mph\n"
        )
        display_weather += f"Humidity: {weather.current.humidity} %\n"
        display_weather += "```"
        await ctx.respond(display_weather)

