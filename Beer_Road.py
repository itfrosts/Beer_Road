"""
This is a solution to the following problem:
You love beer and as the weekend come you want try out as many different beers as possible.
Your helicopter is located @ (LAT, LONG) and it has enough fuel for 2000km.
Create an optimal route to collect as many different beers as you can.

Program takes two command line arguments: latitude, longitude
Data obtained from: github.com/brewdega/open-beer-database-dumps
"""

import geopy.distance, sys, argparse
from collections import namedtuple
import pandas as pd

class Stack():

    def __init__(self):
        self.stack = []

    def get(self):
        return self.stack.pop(0)

    def put(self, item):
        self.stack.insert(0, item)

    def empty(self):
        return len(self.stack) == 0

def calcDist(data, start, end):
    """
    Takes two location IDs and returns the distance between them.
    Args: start, end - location IDs for breweriers - type: int
          data - dataset to look at - type: dict of named tuples
    
    Returns: distance in km - type: float
    """
    coords_1 = (data[start].latitude, data[start].longitude)
    coords_2 = (data[end].latitude, data[end].longitude)
    distance = (geopy.distance.great_circle(coords_1, coords_2).km)
    return distance

def getneighbors(data, startlocation, n = 20):
    """
    Finds the nearest neighbors.
    Args: data - beer dataset - type: dict of namedtuples
          startlocation - ID of current node - type: int
          n - number of potential neighbors - type: int

    Returns: neighbors - subset of data containing n closest neighbors - type: dict of namedtuples
    """
    return sorted(data.values(), key=lambda x: calcDist(data, startlocation, int(x.ID)))[1:n+1]

def DFS_generator(data, start, end, path, dist_travelled, dist_limit):
    """
    Possible path generator using Depth First Search algorithm. Starts looking near distance limit first.
    Args: data - beer dataset - type: dict of namedtuples
          start, end - locations IDs - type: ints
          path - traversed path - type: list
          dist_travelled - type: float
          dist_limit - type: float 
    
    Returns: yields possible path result - type: tuple(list)
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

def number_of_paths(data, n):
    """
    """
    dist_limit = 2000
    dfs_path_set = set()

    gen = DFS_generator(data, data[0].ID, data[0].ID, [], 0, dist_limit)

    # choosing how many possible paths to consider and catching IterationError if there are less possible paths
    while len(dfs_path_set) < n:
        try:
            dfs_path_set.add(next(gen))
        except StopIteration: 
            break
    return dfs_path_set

def uniquebeers(beer_data, path_sets):
    """
    Checks for unique beers in possible route.
    Args: beer_data - contains beer names - type: pandas.DataFrame
          path_sets - possible route - type: tuple(list)

    Returns a tuple of:
        besttrip - best path out of possible routs - type: list
        bestbeers - sorted list of all unique beer names along the path - type: list
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

def print_answer(data, trip, beerlist):
    """
    Prints the answer in the required format.
    
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

def main(home_lat, home_long):
    """
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