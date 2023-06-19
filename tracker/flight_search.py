@flight.child()
@lightbulb.option('flight_id', 'Flight number (no space)')
@lightbulb.command('find', 'Find a flight')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def cmd_find_flight(ctx):
    await ctx.respond('Processing request, hold on')
    call_sign = ctx.options.flightID
    flight_info = find_flight(call_sign)
    await ctx.respond(flight_info)


def get_flights():
    try:
        response = requests.get(f'https://{flight_user_name}:{flight_password}@opensky-network.org/api/states/all')
        response.raise_for_status()
        flight_json = response.json()
        airlines = flight_json.get('states')

        flights = []
        for flight in airlines:
            flights.append({
                "icao": flight[0],
                "flight_number": flight[1],
                "country": flight[2],
                "ground_status": flight[8]
            })
        return flights
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return []


def find_flight(callsign):
    flights = get_flights()

    for flight in flights:
        if callsign in flight["flight_number"]:
            flight_icao = flight["icao"]
            country = flight["country"]
            ground_status = flight["ground_status"]
            break
    else:
        print("Could not find this flight")
        return

    begin = int(time.time() - 100000)
    end = int(time.time())

    try:
        response = requests.get(
            f'https://{flight_user_name}:{flight_password}@opensky-network.org/api/flights/aircraft?icao24={flight_icao}&begin={begin}&end={end}')
        response.raise_for_status()
        airline_info = response.json()[0]
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return

    first_seen = datetime.fromtimestamp(airline_info.get('firstSeen'))
    last_seen = datetime.fromtimestamp(airline_info.get('lastSeen'))
    departure_airport = airline_info.get('estDepartureAirport')
    arrival_airport = airline_info.get('estArrivalAirport')
    vert_distance = airline_info.get('estDepartureAirportVertDistance')
    horiz_distance = airline_info.get('estDepartureAirportHorizDistance')

    display = f'''```json
                Flight: {callsign}
                From: {country}, On Ground Status = {ground_status}
                First seen: {first_seen}, Last seen: {last_seen}
                Departure Airport: {departure_airport}
                Arrival Airport: {arrival_airport if arrival_airport else "Unknown"}
                Departure Vertical Distance: {vert_distance}
                Departure Horizontal Distance: {horiz_distance}
                ```'''
    return display


def flight_data():
    flights = get_flights()
    return [flights[x:x + 20] for x in range(0, len(flights), 20)]
