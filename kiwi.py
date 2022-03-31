import argparse
import csv
import json
from datetime import datetime

all_flights = list()
outbound_routes = list()
round_routes = list()

header = ['flight_no', 'origin', 'destination', 'departure',
          'arrival', 'base_price', 'bag_price', 'bags_allowed']

parser = argparse.ArgumentParser()
parser.add_argument('csv_file', help="Path to the CSV file")
parser.add_argument('origin', help="Origin airport code")
parser.add_argument('destination', help="Destination airport code")
parser.add_argument('--bags', type=int, required=False,
                    default=0, help="Required number of bags")
parser.add_argument('--return', action="store_true",
                    dest='round', help="Round trip")
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
    """Takes file path as input, creates "Flight" objects from rows, appends "all_flights" list with the objects"""
    try:
        with open(file, 'r') as f:
            csvreader = csv.reader(f)
            if next(csvreader) != header:
                raise Exception("The CSV doesn't seem to be correct")
            for row in csvreader:
                all_flights.append(
                    Flight(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]))
    except Exception as e:
        print("The following exception happened:", e)

def flight_difference_in_hours(first_flight, second_flight):
    return (first_flight - second_flight).total_seconds() / 3600

def is_connection(first_flight, second_flight, track, direction):
    """ Takes the current considered flight, possible connecting flight, the track of previous flights and the direction where the flight cannot go.
        Returns with bool that shows if the second flight is possible connection."""
    layover_hours = flight_difference_in_hours(second_flight.departure, first_flight.arrival) if second_flight.departure > first_flight.arrival else 0
    for flight in track:
        if second_flight.destination == flight.origin:
            return False
    return second_flight.origin == first_flight.destination and layover_hours >= 1 and layover_hours < 6 and second_flight.destination != direction


def find_outbound_route():
    """Finds outbound routes between origin and destination, appends it to "outbound_routes" list """
    frontier = [flight for flight in all_flights if flight.origin == args.origin]
    track = list()

    while frontier:

        # Remove the latest flight from the frontier, adds it to current
        current = frontier.pop()

        # Delete previous flights from track if they aren't connections
        for i in range(len(track) - 1, -1, -1):
            if is_connection(track[i], current, track, args.origin):
                break
            track.pop()

        # Add the flight to the track
        track.append(current)

        # Check if the current flight is the destination
        if current.destination == args.destination:
            route = [flight for flight in track]
            outbound_routes.append(route)
            track.pop()
            continue

        # Check for possible connections for the current flight, if there is append it to the frontier
        [frontier.append(flight) for flight in all_flights if is_connection(current, flight, track, args.origin) and flight.bags_allowed >= args.bags]

    return


def find_round_route():
    """Finds return routes between origin and destination, merges the return route to the outbound, appends it to "round_routes" list"""
    for one_way_route in outbound_routes:
        return_origin = one_way_route[-1]
        frontier = [flight for flight in all_flights if flight.origin == return_origin.destination and flight.departure > return_origin.arrival]
        track = list()

        while frontier:

            # Remove the latest flight from the frontier, adds it to current
            current = frontier.pop()

            # Delete previous flights from track if they aren't connections
            for i in range(len(track) - 1, -1, -1):
                if is_connection(track[i], current, track, args.destination):
                    break
                track.pop()

            # Add the flight to the trac
            track.append(current)

            # Check if the current flight is the destination and validate route
            if current.destination == args.origin:
                full_route = [flight for flight in one_way_route]
                [full_route.append(flight) for flight in track]
                round_routes.append(full_route)
                track.pop()
                continue

            # Check for possible connections for the current flight, if there is append it to the frontier
            [frontier.append(flight)
             for flight in all_flights if is_connection(current, flight, track, args.destination)]

    return


def serialize(routes):
    """Takes the list of routes, creates and returns a json object"""
    output = list()
    for route in routes:
        data = dict()
        flight_list = list()
        [flight_list.append(vars(flight)) for flight in route]
        data['flights'] = flight_list
        data['bags_allowed'] = min(
            route, key=lambda x: x.bags_allowed).bags_allowed
        if data['bags_allowed'] < args.bags:
            continue
        data["bags_count"] = args.bags
        data["destination"] = args.destination
        data["origin"] = args.origin
        data["total_price"] = sum(
            bag.bag_price * args.bags for bag in route) + sum(flight.base_price for flight in route)
        data["travel_time"] = route[-1].arrival - route[0].departure if len(route) > 1 else route[0].arrival - route[0].departure
        output.append(data)
    return sorted(output, key=lambda x: x['total_price'])


if __name__ == "__main__":
    import_csv(args.csv_file)
    find_outbound_route()
    if args.round:
        find_round_route()
        print(json.dumps(serialize(round_routes), indent=4, default=str)) if len(
            round_routes) > 0 else print('No round trip is possible between origin and destination')
    else:
        print(json.dumps(serialize(outbound_routes), indent=4, default=str)) if len(
            outbound_routes) > 0 else print('No route is possible between origin and destination')
