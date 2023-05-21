@bot.command
@lightbulb.option('fid', 'Flight number (no space)')
@lightbulb.command('flightfind', 'Find a flight')
@lightbulb.implements(lightbulb.SlashCommand)
async def cmd_find_flight(ctx):
    await ctx.respond('Processing request, hold on')
    call_sign = ctx.options.fid
    flight_info = find_flight(call_sign)
    display = ''
    display += flight_info
    await ctx.respond(display)

def flight_data():
    icao_list = get_flights()[0]
    flight_list = get_flights()[1]
    country_list = get_flights()[2]
    ground_list = get_flights()[3]
    new_icao_list = [icao_list[x:x + 20] for x in range(0, len(icao_list), 20)]
    new_flight_list = [flight_list[x:x + 20] for x in range(0, len(flight_list), 20)]
    new_country_list = [country_list[x:x + 20] for x in range(0, len(country_list), 20)]
    new_ground_list = [ground_list[x:x + 20] for x in range(0, len(ground_list), 20)]
    return new_icao_list, new_flight_list, new_country_list, new_ground_list
