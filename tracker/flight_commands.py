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


@bot.command
@lightbulb.option('page', 'Page number')
@lightbulb.command('flightall', 'Show all flights (global)')
@lightbulb.implements(lightbulb.SlashCommand)
async def show_all_flights(ctx):
    await ctx.respond('Processing request, hold on')
    icao_all = flight_data()[0]
    flight_all = flight_data()[1]
    country_all = flight_data()[2]
    ground_all = flight_data()[3]
    index = int(ctx.options.page)
    selected_icao = icao_all[index]
    selected_flight = flight_all[index]
    selected_country = country_all[index]
    selected_ground = ground_all[index]
    display = '```'
    display += 'Flight # |   Departure Country   | On Ground   | ICAO24 ID\n'
    # display += '----------------------------------------------\n'
    for i in range(len(selected_flight)):
        display += '{0:9s}|   {1:19s} | {2:10s}  | {3:9s}\n'.format(selected_flight[i], selected_country[i],
                                                                    str(selected_ground[i]), selected_icao[i])
    display += '```'
    print(display)
    await ctx.respond(display)
