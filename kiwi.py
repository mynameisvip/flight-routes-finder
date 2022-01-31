"""TODO:refactor"""

import csv
import argparse
from datetime import datetime
import json


flights = list()
possible_routes = list()
possible_round_routes = list()
header = ['flight_no', 'origin', 'destination', 'departure',
          'arrival', 'base_price', 'bag_price', 'bags_allowed']

parser = argparse.ArgumentParser()
parser.add_argument('csv_file', help="Path to the CSV file")
parser.add_argument('departure', help="Departure airport code")
parser.add_argument('destination', help="Destination airport code")
parser.add_argument('-b', '--bags', type=int, required=False,
                    default=0, help="Required number of bags")
parser.add_argument('-r', '--round', '--return',action="store_true",
                    help="Round trip")
args = parser.parse_args()


class Flight:
    def __init__(self, flight_no, origin, destination, departure, arrival, base_price, bag_price, bags_allowed):
        self.flight_no = flight_no
        self.origin = origin
        self.destination = destination
        self.departure = datetime.strptime(departure, '%Y-%m-%dT%H:%M:%S')
        self.arrival = datetime.strptime(arrival, '%Y-%m-%dT%H:%M:%S')
        self.base_price = float(base_price)
        self.bag_price = float(bag_price)
        self.bags_allowed = int(bags_allowed)


def import_csv(file):
    try:
        with open(file, 'r') as f:
            csvreader = csv.reader(f)
            if next(csvreader) != header:
                raise Exception("The CSV doesn't seem to be correct")
            for row in csvreader:
                flights.append(
                    Flight(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]))
    except Exception as e:
        print("The following exception happened:", e)


def is_connection(first_flight, second_flight, track, direction):
    layover_hours = (second_flight.departure - first_flight.arrival).total_seconds() / \
        3600 if second_flight.departure > first_flight.arrival else 0
    for flight in track:
        if second_flight.destination == flight.origin:
            return False
    return second_flight.origin == first_flight.destination and layover_hours >= 1 and layover_hours < 6 and second_flight.destination != direction


def find_route():
    frontier = [flight for flight in flights if flight.origin ==
                args.departure and flight.bags_allowed >= args.bags]

    track = list()

    while 1:

        #Check if there is no more possible flight on the list to be checked
        if len(frontier) == 0:
            return

        #Remove the latest flight from the frontier
        current = frontier.pop()

        #Delete previous flights from track if they aren't connections
        for i in range(len(track) - 1, -1, -1):
            if is_connection(track[i], current, track, args.departure):
                break
            track.pop()

        #Add the flight to the track
        track.append(current)

        #Check if the current flight is the destination
        if current.destination == args.destination:
            route = [flight for flight in track]
            possible_routes.append(route)
            track.pop()
            continue

        #Check for possible connections for the current flight, if there is append it to the frontier
        [frontier.append(flight)
         for flight in flights if is_connection(current, flight, track, args.departure) and flight.bags_allowed >= args.bags]


def find_round():
    for one_way_route in possible_routes:
        return_origin = one_way_route[-1]
        frontier = [flight for flight in flights if flight.origin == return_origin.destination and flight.departure > return_origin.arrival and return_origin.bags_allowed >= args.bags]
        track = list()

        while 1:

            #Check if there is no more possible flight on the list to be checked
            if len(frontier) == 0:
                break

            #Remove the latest flight from the frontier
            current = frontier.pop()

            #Delete previous flights from track if they aren't connections
            for i in range(len(track) - 1, -1, -1):
                if is_connection(track[i], current, track, args.destination):
                    break
                track.pop()

            #Add the flight to the trac
            track.append(current)

            #Check if the current flight is the destination and validate route
            if current.destination == args.departure:
                full_route = [flight for flight in one_way_route]
                [full_route.append(flight) for flight in track]
                possible_round_routes.append(full_route)
                track.pop()
                continue

            #Check for possible connections for the current flight, if there is append it to the frontier
            [frontier.append(flight)
             for flight in flights if is_connection(current, flight, track, args.destination) and flight.bags_allowed >= args.bags]


def serialize(routes):
    output = list()
    for route in routes:
        data = dict()
        flightlist = list()
        for flight in route:
            flightlist.append(vars(flight))
        
        data['flights'] = flightlist
        data['bags_allowed'] = min(
            route, key=lambda x: x.bags_allowed).bags_allowed
        data["bags_count"] = args.bags
        data["destination"] = args.destination
        data["origin"] = args.departure
        data["total_price"] = sum(
            bag.bag_price * args.bags for bag in route) + sum(flight.base_price for flight in route)
        data["travel_time"] = route[-1].arrival - \
            route[0].departure if len(
                route) > 1 else route[0].arrival - route[0].departure
        output.append(data)
    return  sorted(output, key=lambda x: x['total_price'])


if __name__ == "__main__":
    import_csv(args.csv_file)
    find_route()
    if args.round:
        find_round()
        print(json.dumps(serialize(possible_round_routes), indent=4, default=str))
    else:
        print(json.dumps(serialize(possible_routes), indent=4, default=str))
