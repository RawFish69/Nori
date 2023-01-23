@bot.command
@lightbulb.option('location', 'Name of the city')
@lightbulb.command('weather', 'Checks the weather status of a city')
@lightbulb.implements(lightbulb.SlashCommand)
async def check_weather(ctx):
    city = ctx.options.location
    async with python_weather.Client(format=python_weather.IMPERIAL) as client:
        weather = await client.get(city)
    temp_C = int((weather.current.temperature - 32) * 5 / 9)
    feels_like_F = weather.current.feels_like
    feels_like_C = int((feels_like_F - 32) * 5 / 9)
    display_weather = f'```City/Area: {city}\n'
    display_weather += f'Local Date: {weather.current.utc_time.month}/{weather.current.utc_time.day}/{weather.current.utc_time.year}\n'
    display_weather += f'Region: {weather.nearest_area.region}, {weather.nearest_area.country}\n'
    display_weather += f"Current Temperature: {weather.current.temperature} F or {temp_C} C\n"
    display_weather += f'Feels like {feels_like_F} F or {feels_like_C} C\n'
    display_weather += 'Upcoming Temperature\n'
    for forecast in weather.forecasts:
        display_weather += (
            f'{forecast.date} Highest Temp: {forecast.highest_temperature} F Lowest Temp: {forecast.lowest_temperature} F\n')
    display_weather += f'Wind Direction: {weather.current.wind_direction}, Wind Speed: {weather.current.wind_speed} km/h\n'
    display_weather += f'Humidity: {weather.current.humidity} %\n'
    display_weather += '```'
    print(display_weather)
    await ctx.respond(display_weather)
