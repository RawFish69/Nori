# Sample code of how nori handles user message prompt and respond
import requests


@bot.listen()
async def on_message_response(event: hikari.MessageCreateEvent):
    response_permission = False
    for channel in channel_whitelist:
        if event.channel_id == channel:
            response_permission = True
    if event.is_bot or not event.content:
        return
    if response_permission == True:
        gpt_endpoint = "https://api.openai.com/v1/chat/completions"
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
        if 'gpt' in engine.lower():
            data = {
                "model": engine,
                "messages": [
                    {"role": "system", "content": "Behavior of AI"},
                    {"role": "assistant", "content": "Sample"},
                    {"role": "user", "content": f"{prompt}"},
                ],
                "max_tokens": 500,
                "temperature": 0.5,
                "top_p": 1,
            }
            # Send request
            response = requests.post(gpt_endpoint, headers=headers, json=data)
            # Extract response text
            result = response.json()
            generated_text = result["choices"][0]["message"]["content"]
            print(f'AI Response: {generated_text}')
            await event.message.respond(generated_text)
        else:
            data = {
                "model": engine,
                "prompt": prompt,
                "max_tokens": 450,
                "temperature": 0.5,
                "top_p": 1,
            }
            # Send request
            response = requests.post(endpoint, headers=headers, json=data)
            # Extract response text
            result = response.json()
            generated_text = result["choices"][0]["text"]
            print(f'AI Response: {generated_text}')
            await event.message.respond(generated_text)
    else:
        print(f'[No Rely Access] {event.author}: {event.content}')
