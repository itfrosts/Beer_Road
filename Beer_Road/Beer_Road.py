"""
This is a solution to the following problem:
You love beer and as the weekend come you want try out as many different beers as possible.
Your helicopter is located @ (LAT, LONG) and it has enough fuel for 2000km.
Create an optimal route to collect as many different beers as you can.

Program takes two command line arguments: latitude, longitude
Data obtained from: github.com/brewdega/open-beer-database-dumps
"""

import argparse
import pandas as pd
from collections import namedtuple
from math import sin, cos, sqrt, asin, radians
from typing import Dict, Tuple, List, Iterator, Set

class Stack():

    def __init__(self):
        self.stack = []

    def get(self):
        return self.stack.pop(0)

    def put(self, item):
        self.stack.insert(0, item)

    def empty(self):
        return len(self.stack) == 0

def calcDist(data: Dict[int, Tuple], start: int, end: int) -> int:
    """
    Returns the distance in km between two locations using Harversine formula.

    Args: 
        data: dataset with location IDs, latitude and longitude coordinates.
        start: ID number of the location at starting point.
        end: ID  number of the location at the end point.  end - location IDs for breweriers - type: int
    """
    lat1, lon1, lat2, lon2 = map(radians, [data[start].latitude, data[start].longitude, data[end].latitude, data[end].longitude])

    dif_lat = lat2 - lat1
    dif_lon = lon2 - lon1

    a = sin(dif_lat/2)**2 + cos(lat1) * cos(lat2) * sin(dif_lon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371 # Radius of Earth in km
    return int(c * r)

def getneighbors(data: Dict[int, Tuple], startlocation: int, n=20) -> Dict[int, Tuple]:
    """
    Returns n nearest neighbors of a given location.

    Args: 
        data: dataset containing location IDs, latitude and longitude coordinates.
        startlocation: ID of the current location.
        n: number of neighbors to return.
    """
    return sorted(data.values(), key=lambda x: calcDist(data, startlocation, int(x.ID)))[1:n+1]

def DFS_generator(data: Dict[int, Tuple], start: int, end: int, path: List[int], dist_travelled: int, dist_limit: int) -> Iterator[List[int]]:
    """
    Generates a possible path using depth first search algorithm.
    
    Args: 
        data: dataset containing location IDs, latitude and longitude coordinates.
        start: ID of the starting location.
        end: ID of the final location.
        path: list of traversed nodes.
        dist_travelled: sum of travelled distance.
        dist_limit: limit of total distance.
    
    Yields: 
        A list of all the visited nodes from start to end.
    """
    from_stack = Stack()
    from_stack.put((data, start, end, path, dist_travelled, dist_limit))

    while not from_stack.empty():
        data, current, home, path, dist_travelled, dist_limit = from_stack.get()

        if (dist_travelled > dist_limit):
            continue

        if current == home and dist_travelled > dist_limit/2:
            # route done - yield result
            yield tuple(path + [current])
        
        if current in path:
            continue

        for neighbor in getneighbors(data, current):
            from_home_to_nbr = dist_travelled + calcDist(data,current, neighbor.ID) 
            direct_nbr_to_home = calcDist(data, neighbor.ID, home)
            want_home_now = dist_travelled + calcDist(data, current, home)

            # checking if I can return home from neighbor, if not, time to go home
            if (from_home_to_nbr + direct_nbr_to_home) > dist_limit:
                if want_home_now < dist_limit:
                    neighbor = data[0]
                    dist_travelled = want_home_now
                else:
                    continue
                
            from_stack.put((data, neighbor.ID, end, path + [current], from_home_to_nbr, dist_limit))

def number_of_paths(data: Dict[int, Tuple], n: int) -> Set[int]:
    """
    Returns a set of n possible paths generated using DFS_generator. 

    Args:
        data: dataset containing location IDs, latitude and longitude coordinates.
        n: number of possible paths. 
    """
    dist_limit = 2000
    dfs_path_set = set()

    gen = DFS_generator(data, data[0].ID, data[0].ID, [], 0, dist_limit)

    while len(dfs_path_set) < n:
        try:
            dfs_path_set.add(next(gen))
        except StopIteration: 
            break
    return dfs_path_set

def uniquebeers(beer_data: pd.DataFrame, path_sets: Set[int]) -> Tuple[List, List]:
    """
    Checks for unique beers in possible route.

    Args: 
        beer_data: pandas.DataFrame containing beer names associated with brewery IDs.
        path_sets: a set of n possible paths.

    Returns:
        besttrip: best path from the considered n routes. 
        bestbeers: sorted list of unique beers collected along the path.
    """
    bestbeers = []
    besttrip = []
    for trip in path_sets:
        beerlist = []
        for destination in trip:
            brewery_serves = beer_data[beer_data['brewery_id']==destination]['name'].values
            for beer_name in brewery_serves:
                if beer_name not in beerlist:
                    beerlist.append(beer_name)
        if len(beerlist) > len(bestbeers):
            bestbeers = beerlist
            besttrip = trip
    return (besttrip, sorted(bestbeers))

def print_answer(data: Dict[int, Tuple], trip: List[int], beerlist: List[str]) -> None:
    """
    Prints the answer in the required format.

    Args:
        data: dataset containing location IDs, latitude and longitude coordinates.
        trip: list of node IDs visited along the path.
        beerlist: list of unique beers collected along the path.
    """
    cntr1 = 0
    num1 = 0
    total_distance = 0
    dist_between_stops = 0
    print(f'You have {len(trip)-2} breweries on your itinerary:')
    for stop in trip:
        if num1 > 0:
           dist_between_stops = int(calcDist(data, trip[num1-1], trip[num1]))
           total_distance += int(calcDist(data, trip[num1-1], trip[num1]))
        if stop == 0:
            if cntr1 == 0:
                print(f'[HOME] >> latitude: {data[stop].latitude}, longitude: {data[stop].longitude}')
                cntr1 += 1    
            else:
                print(f'[HOME] >> latitude: {data[stop].latitude}, longitude: {data[stop].longitude}, distance: {dist_between_stops}km')
                print(f'\nTotal distance of the journey is {total_distance}km')
        else: 
            print(f'[{stop}] {data[stop].name} >> latitude: {data[stop].latitude}, longitude: {data[stop].longitude}, distance: {dist_between_stops}km')
        num1+=1
    print(f'\n\nCollected {len(beerlist)} beer types:')
    print("\n".join(str(beer) for beer in beerlist))

def main(home_lat: int, home_long: int) -> None:
    """
    Arranges previously defined functions, solves the question and outputs the result.

    Args:
        home_lat: latitude coordinate input from command line.
        home_long: longitude coordinate input from command line.
    """
    #importing and cleaning data
    beer_df = pd.read_csv('https://raw.githubusercontent.com/brewdega/open-beer-database-dumps/master/dumps/beers.csv').drop_duplicates()
    brewery_df = pd.read_csv('https://raw.githubusercontent.com/brewdega/open-beer-database-dumps/master/dumps/breweries.csv', index_col = 'id')
    geo_df = pd.read_csv('https://raw.githubusercontent.com/brewdega/open-beer-database-dumps/master/dumps/geocodes.csv', index_col = 'brewery_id')

    brewery_df = brewery_df[~brewery_df.index.duplicated(keep='first')]
    geo_df = geo_df[~geo_df.index.duplicated(keep='first')]
    
    #creating a namedtuple for better performance
    Location = namedtuple("Location", "ID name latitude longitude".split())
    data = {}
    for idx, row in brewery_df.iterrows():
        name = row['name']
        if idx in geo_df.index.values:
            latitude = geo_df.at[idx, 'latitude']
            longitude = geo_df.at[idx, 'longitude']
        data[idx] = Location(idx, name, latitude, longitude)

    #adding home location to the list
    data[0] = Location(0, "Home", home_lat, home_long) 
    
    dfs_path_set = number_of_paths(data, 50)
    
    trip, beerlist = uniquebeers(beer_df, dfs_path_set)
        
    print_answer(data, trip, beerlist)

if __name__ == "__main__":
    #taking care of the input at command line
    parser = argparse.ArgumentParser()
    parser.add_argument("lat", type=float, help="latitude coordinate")
    parser.add_argument("long", type=float, help="longitude coordinate")
    args = parser.parse_args()
    assert (args.lat > -90 and args.lat < 90) and (args.long > -180 or args.long < 180), "Coordinates are invalid"

    main(args.lat, args.long)