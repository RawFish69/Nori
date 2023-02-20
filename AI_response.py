# Sample code of how nori handles user message prompt and respond
import requests


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
