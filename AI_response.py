# Sample code of how nori handles user message prompt and respond
import requests


# For model gpt-3.5 or above
@bot.listen()
async def AI_response(event: hikari.MessageCreateEvent):
    response_permission = False
    for channel in channel_whitelist:
        if event.channel_id == channel:
            response_permission = True

    # print(event.content)
    # if event.is_bot or not event.content:
    #     return
    if response_permission == True:
        endpoint = "https://api.openai.com/v1/chat/completions"
        # API key
        api_key = AI_API_KEY
        # Input data
        prompt = event.content
        # Request headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        # Request data
        data = {
            "model": engine,
            "messages": [
                {"role": "system", "content": "Behavior of AI"},
                {"role": "assistant", "content": "Sample."},
                {"role": "user", "content": f"{prompt}"},
            ],
            "max_tokens": 500,
            "temperature": 0.5,
            "top_p": 1,
        }
        # Send request
        response = requests.post(endpoint, headers=headers, json=data)
        # Extract response text
        result = response.json()
        generated_text = result["choices"][0]["message"]["content"]
        print(f'AI Reponse: {generated_text}')


# For models like davinci-003, etc

@bot.listen()
async def on_message_response(event: hikari.MessageCreateEvent):
    response_permission = False
    for channel in channel_whitelist:
        if event.channel_id == channel:
            response_permission = True

    # print(event.content)
    if event.is_bot or not event.content:
        return
    if response_permission == True:
        print(f'[Access Granted] {event.author}: {event.content}')
        endpoint = "https://api.openai.com/v1/completions"
        # API key
        api_key = AI_API_KEY
        # Input data
        prompt = event.content
        # Request headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        # Request data
        data = {
            "model": engine,
            "prompt": prompt,
            "max_tokens": 300,
            "temperature": 0.5,
            "top_p": 1,
        }
        # Send request
        response = requests.post(endpoint, headers=headers, json=data)
        # Extract response text
        result = response.json()
        generated_text = result["choices"][0]["text"]
        print(f'AI Reponse: {generated_text}')
        await event.message.respond(generated_text)
    else:
        print(f'[No Rely Access] {event.author}: {event.content}')
