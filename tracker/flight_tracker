user_name = ''
password = ''

def get_flights():
    get_api = requests.get(f'https://{user_name}:{password}@opensky-network.org/api/states/all')
    flight_json = get_api.json()
    airlines = flight_json.get('states')
    # flight_data = json.dumps(airlines, indent=5)
    icao_list = []
    flgiht_number = []
    country_list = []
    ground_status = []
    for flight in airlines:
        icao_list.append(flight[0])
        flgiht_number.append(flight[1])
        country_list.append(flight[2])
        ground_status.append(flight[8])
    return icao_list, flgiht_number, country_list, ground_status


def find_flight(callsign):
    icao = get_flights()[0]
    flight_list = get_flights()[1]
    country_list = get_flights()[2]
    ground = get_flights()[3]
    # index = 0
    # for flight in flight_list:
    #     if callsign in flight:
    #         break
    #     else:
    #         index += 1
    flight_icao = ''
    country = ''
    ground_status = False
    for i in range(len(icao)):
        if callsign in flight_list[i]:
            flight_icao = icao[i]
            country = country_list[i]
            ground_status = ground[i]
            break
        elif flight_list[i] == '':
            pass
        # elif callsign != flight_list[i]:
            # print(icao[i], flight_list[i])
        elif i > len(icao):
            print('Could not find this flight')
            break
    # flight_icao = icao[index]
    print(flight_icao)
    begin = int(time.time() - 100000)
    end = int(time.time())
    get_airline = requests.get(f'https://{user_name}:{password}@opensky-network.org/api/flights/aircraft?icao24={flight_icao}&begin={begin}&end={end}')
    print(get_airline)
    airline_info = get_airline.json()
    airline_data = (airline_info)[0]
    print(airline_data)
    airline_json = json.dumps(airline_data, indent=5)
    print(airline_json)
    display = '```'
    first_seen = datetime.fromtimestamp(airline_data.get('firstSeen'))
    last_seen = datetime.fromtimestamp(airline_data.get('lastSeen'))
    departure_airport = airline_data.get('estDepartureAirport')
    arrival_airport = airline_data.get('estArrivalAirport')
    flight_num = callsign
    vert_distance = airline_data.get('estDepartureAirportVertDistance')
    horiz_distance = airline_data.get('estDepartureAirportHorizDistance')
    display += f'Flight: {flight_num}\n'
    display += f'From: {country}, On_Ground_Status = {ground_status}\n'
    display += f"First seen: {first_seen}, Last seen: {last_seen}\n"
    display += f'Departure Airport: {departure_airport}\n'
    if arrival_airport != 'null':
        display += f'Arrival Airport: {arrival_airport}\n'
    else:
        display += 'Arrival Airport: Unknown\n'
    display += f'Departure veritcal distance: {vert_distance}\n'
    display += f'Departure horizontal distance: {horiz_distance}\n'
    display += '```'
    return display

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
