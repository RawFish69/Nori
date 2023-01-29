@bot.command
@lightbulb.option('location', 'Name of the city')
@lightbulb.command('weather', 'Checks the weather status of a city')
@lightbulb.implements(lightbulb.SlashCommand)
async def check_weather(ctx):
    city = ctx.options.location
    async with python_weather.Client(format=python_weather.IMPERIAL) as client:
        weather = await client.get(city)
    hourly_data = []
    the_dates = []
    forecast_data = []
    temp_C = int((weather.current.temperature - 32) * 5 / 9)
    feels_like_F = weather.current.feels_like
    feels_like_C = int((feels_like_F - 32) * 5 / 9)
    display_weather = f'```City/Area: {city}\n'
    display_weather += f'Local Date: {weather.current.utc_time.month}/{weather.current.utc_time.day}/{weather.current.utc_time.year}\n'
    display_weather += f'Region: {weather.nearest_area.region}, {weather.nearest_area.country}\n'
    display_weather += f"Current Temperature: {weather.current.temperature} F or {temp_C} C\n"
    display_weather += f'Feels like {feels_like_F} F or {feels_like_C} C\n'
    for forecast in weather.forecasts:
        the_dates.append(forecast.date)
        hourly_data.clear()
        for hourly in forecast.hourly:
            hourly_data.append(f'[{hourly.time.hour}:{hourly.time.minute}{hourly.time.second}] {hourly.description}')
        forecast_data.append(hourly_data)
    index = 1
    display_weather += f'{the_dates[0]} (Today):\n'
    for var in forecast_data[0]:
        if index < 2:
            display_weather += f'{var} -> '
            index += 1
        else:
            display_weather += f'{var}\n'
            index = 1
    display_weather += f'Wind Direction: {weather.current.wind_direction}, Wind Speed: {weather.current.wind_speed} mph\n'
    display_weather += f'Humidity: {weather.current.humidity} %\n'
    display_weather += '```'
    print(display_weather)
    await ctx.respond(display_weather)
