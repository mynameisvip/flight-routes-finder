"""TODO: algorithm, serialization """

import csv
import argparse
from datetime import datetime

flights = list()
possible_routes = list()
header = ['flight_no', 'origin', 'destination', 'departure',
          'arrival', 'base_price', 'bag_price', 'bags_allowed']

parser = argparse.ArgumentParser()
parser.add_argument('csv_file', help="Path to the CSV file")
parser.add_argument('departure', help="Departure airport code")
parser.add_argument('destination', help="Destination airport code")
parser.add_argument('-b', '--bags', type=int, required=False,
                    default=0, help="Required number of bags")
parser.add_argument('-r', '--return', type=bool, required=False,
                    default=False, help="Round trip")
args = parser.parse_args()


class Flight:
    def __init__(self, flight_no, origin, destination, departure, arrival, base_price, bag_price, bags_allowed):
        self.flight_no = flight_no
        self.origin = origin
        self.destination = destination
        self.departure = datetime.strptime(departure, '%Y-%m-%dT%H:%M:%S')
        self.arrival = datetime.strptime(arrival, '%Y-%m-%dT%H:%M:%S')
        self.base_price = base_price
        self.bag_price = bag_price
        self.bags_allowed = bags_allowed

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

def is_connection(first_flight, second_flight):
    layover_hours = (second_flight.departure - first_flight.arrival).total_seconds() / \
                3600 if second_flight.departure > first_flight.arrival else 0
    return second_flight.origin == first_flight.destination and layover_hours > 1 and layover_hours < 6


def find_path(all_flights):
    frontier = [x for x in all_flights if x.origin == args.departure]
    track = list()

    while True:

        #Check if there is no more possible flight on the list to be checked RETURN HERE, something wrong
        if len(frontier) == 0:
            return 

        current = frontier.pop()

        #Delete previous flights from track if they aren't connections
        for i in range(len(track) -1,-1,-1):
            if is_connection(track[i], current):
                break
            track.pop()

        track.append(current)

        #Check if the current flight is the destination
        if current.destination == args.destination:
            route = list()
            for x in track:
                route.append(x)
            possible_routes.append(route)
            track.pop()
            continue

        #Check for possible connections for the current flight, if there is append it to the frontier
        for f in all_flights:
            if is_connection(current,f):
                frontier.append(f)

if __name__ == "__main__":
    import_csv(args.csv_file)
    print(len(flights))
    find_path(flights)
    # TEST
    for i in possible_routes:
        print('Route:')
        for x in i:
            print(x.flight_no)
