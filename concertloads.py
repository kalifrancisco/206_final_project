import requests
import json
import sqlite3
from bs4 import BeautifulSoup 
from requests import get, auth
from pprint import pprint
from math import radians, sin, cos, sqrt, asin


def get_seatgeek_data(postal_code, mi_range, start_date, end_date):

    CLIENT_ID = "MjY1NDE4Mzd8MTY4MTk1NDUwMC44MDkzOTk2"
    APP_SECRET = "8e4c9d4ebe18b3fb44fe5b6c1c55c0993ac1efa46f92c0fc78520440a5c114af"
    ENDPOINT = "events"

    url = f"https://api.seatgeek.com/2/{ENDPOINT}"

    # Define URL parameters here

    params = {
        'client_id': CLIENT_ID,
        'client_secret': APP_SECRET,
        'postal_code': postal_code,
        'range': mi_range,
        'datetime_utc.gte': start_date,
        'datetime_utc.lte': end_date,
        'per_page': 100
    }

    resp = get(url=url, params=params)
    raw_data_dct = resp.json()
    event_lst = []

    for event in raw_data_dct["events"]:
        event_lst.append(event)

    return event_lst





def create_seatgeek_db(event_lst):

    conn = sqlite3.connect('seatgeek_events.db')
    c = conn.cursor()

    # test_lst = [] #debug

    # Create a table to store the data
    c.execute('''CREATE TABLE IF NOT EXISTS seatgeek_events
                 (performer, event_type, venue, latitude, longitude)''')

    # Loop through each event in the list and insert data into the table
    count = 0
    # print(len(event_lst))

    for event in event_lst:

        if count == 25:
            break

        performer_name = event['performers'][0]['name']
        event_type = event['type']
        if '_' in event_type:
            event_type = event_type.replace('_', ' ')
        location_name = event["venue"]["name"]

        # log percise location data for transit api
        lat = event["venue"]["location"]["lat"]
        lon = event["venue"]["location"]["lon"]

        c.execute("SELECT * FROM seatgeek_events WHERE performer=? AND event_type=? AND venue=?", 
                  (performer_name, event_type, location_name))
        result = c.fetchone()


        if result is not None:
            # data already exists, skip insertion
            # print("NOT INPUTTING:" + str(result))
            continue
        else:
            # insert data into table
            # print("INSERTING!!")
            # print(count)
            c.execute("INSERT INTO seatgeek_events VALUES (?, ?, ?, ?, ?)", (performer_name, event_type, location_name, lat, lon))
            count += 1

    #c.execute('''DELETE FROM seatgeek_events WHERE rowid NOT IN 

    #             (SELECT min(rowid) FROM seatgeek_events GROUP BY performer, event_type, venue, latitude, longitude)''')

    conn.commit()
    conn.close()


def nearest_stop(api_key):  
    endpoint = 'https://api.transit.land/api/v1/stops'

    TRANSPORT_API_PARAMS = {
        "per_page": 100
    }

    conn = sqlite3.connect('seatgeek_events.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS transportation_data
                 (stop_name TEXT, lat_cord INTEGER, lon_cord INTEGER, wheelchair_access TEXT, venue_name TEXT)''')
    c.execute("SELECT performer, event_type, venue, latitude, longitude FROM seatgeek_events")
    rows = c.fetchall()

    stops_count = 1

    for row in rows:
        if stops_count > 100:
            break

        venue_name = row[2]
        lat = row[3]
        lon = row[4]

        params = {
            'lat': lat,
            'lon': lon,
            'r': 1000,
            'per_page': 1,
            'api_key': api_key
        }

        headers = {"Api-Key": api_key}
        resp = requests.get(endpoint, headers=headers, params=params)
        #print(resp.json())

        if resp.status_code == 401:
            print("Invalid API key")
        elif resp.status_code == 429:
            print("Rate limit exceeded")

        # move to next page of data in transit API
        if 'meta' in resp.json():
            if 'next' in resp.json()['meta']:
                resp = requests.get(resp.json()['meta']['next'], headers=headers)
                data = resp.json()
        else:
            break

        for stop in data["stops"]:
            data_cords = stop["geometry"]["coordinates"]
            lat_c = data_cords[1]
            lon_c = data_cords[0]
            stop_name = stop['name']
            wheelchair = stop["wheelchair_boarding"]
            # print(stop_name, lat_c, lon_c, str(wheelchair), str(venue_name)) # debug

            c.execute("INSERT INTO transportation_data VALUES (?, ?, ?, ?, ?)", (stop_name, lat_c, lon_c, str(wheelchair), str(venue_name)))
            conn.commit()
            break 

        stops_count += 1
        params['per_page'] = 1

    conn.commit()
    conn.close()


# integrate closest resturant rec based on lat/lon of stop:
def generate_food_recs(api_key, budget, la, lo):
    ep = 'https://api.yelp.com/v3/businesses/search'
    yelp_lst = []

    headers = {'Authorization': f'Bearer {api_key}'}
    params = {
        'term': 'restaurant',
        'latitude': la,
        'longitude': lo,
        'radius': 1000,
        'price': budget,
        'sort_by': 'rating',
        'limit': 1
    }

    response = requests.get(ep, headers=headers, params=params)
    yelp_data = response.json()
    rest_name = yelp_data["businesses"][0]["name"]
    lat = yelp_data["businesses"][0]["coordinates"]["latitude"]
    lon = yelp_data["businesses"][0]["coordinates"]["longitude"]

    yelp_lst.append(rest_name)
    yelp_lst.append(lat)
    yelp_lst.append(lon)

    return yelp_lst


def add_distance_column(lat1, lon1, lat2, lon2):
     # use haversine formula to convert euclidian distance between 2 cords into miles
     
    r = 3959 # rad of Earth
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return r * c


# OLD DIST:
# def add_distance_column(one, two, three, four):
#      # use haversine formula to convert euclidian distance between 2 cords into miles
     
#     first = [one, two]
#     second = [three, four]
#     distance = math.dist(first, second)
#     return distance



def join_databases():

    conn1 = sqlite3.connect('seatgeek_events.db')
    c1 = conn1.cursor()
    conn2 = sqlite3.connect('transportation_data.db')
    c2 = conn2.cursor()

    # Create new table to store our combined data
    c1.execute('''CREATE TABLE IF NOT EXISTS joined_data

                 (performer TEXT, event_type TEXT, venue TEXT, latitude INTEGER, longitude INTEGER, stop_name TEXT, lat_cord INTEGER, lon_cord INTEGER, wheelchair_access TEXT, transit_distance INTEGER, restaurant_name INTEGER, restaurant_distance INTEGER)''')


    # if venue_name and venue are equal, store data together
    c1.execute('''SELECT seatgeek_events.performer, seatgeek_events.event_type, seatgeek_events.venue, seatgeek_events.latitude, seatgeek_events.longitude, transportation_data.stop_name, transportation_data.lat_cord, transportation_data.lon_cord, transportation_data.wheelchair_access, COUNT(*) as count
                  FROM seatgeek_events 
                  JOIN transportation_data 
                  ON seatgeek_events.venue = transportation_data.venue_name
                  GROUP BY seatgeek_events.venue
                  HAVING count = 1''')

    rows = c1.fetchall()
    # loop through data and insert it into new table
    for row in rows:
        performer = row[0]
        event_type = row[1]
        venue = row[2]
        latitude = row[3]
        longitude = row[4]
        stop_name = row[5]
        lat_cord = row[6]
        lon_cord = row[7]
        wheelchair_access = row[8]
        transit_distance = add_distance_column(latitude, longitude, lat_cord, lon_cord)

        # YELP FUSION API ADDITION:
        yelp_lst = generate_food_recs('WRRtreepKK6FHXb9IHVirJ0ZolgQVE0xopdBsZAqNznG0LJ5i16faQGUEpBLzX2tLKj2oQstYbkbzre5HjXFU5xE2cwCmpY1pwnxJtASd1FbynJnnYxu_sJD7q5BZHYx', 2, lat_cord, lon_cord)
        rest_name = yelp_lst[0]
        rest_lat = yelp_lst[1]
        rest_lon = yelp_lst[2]
        rest_distance = add_distance_column(latitude, longitude, rest_lat, rest_lon)

        c1.execute("INSERT INTO joined_data VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (performer, event_type, venue, latitude, longitude, stop_name, lat_cord, lon_cord, wheelchair_access, transit_distance, rest_name, rest_distance))

        conn1.commit()

    conn1.close()
    conn2.close()

# write distance calculations for each venue to a new text file
def write_to_file():
    f = open("distance_calculations.txt", "w")
    conn = sqlite3.connect('seatgeek_events.db')
    c = conn.cursor()

    c.execute("SELECT venue, stop_name, transit_distance, restaurant_name, restaurant_distance FROM joined_data")
    rows = c.fetchall()

    f.write("Venue, Name of Stop, Transit Distance (mi), Nearest Restaurant, Restaurant Distance (mi) \n")

    for row in rows:
        f.write("Name of Venue: " + str(row[0]) + ", Name of Stop: " + str(row[1]) + ", Distance between: " + str(row[2]) + ", Restaurant Name: " + str(row[3]) + ", Distance Between Stop & Restaurant: " + str(row[4]) + "\n")

    f.close()
    return

def main():
    # 1 - get lat + lon from seatgeek db (last two rows)
    # 2 - use that lat & lon using 'SELECT' to get lat and lon to ask transitland api about
    # 3 - add into transitland db w/ shared integer key
    # 4 - calculate something using distance and some data from transitland api
    # 5 - visualizations between concert location & bus stop (distance calculation)

    post_code = '10001'
    mi_range = '100mi'
    start_date = '2023-05-01'
    end_date = '2023-10-28'

    '''
    # needs to increment by 1 every time main is called
    conn = sqlite3.connect('seatgeek_events.db')
    c = conn.cursor()
    # Get the size of the 'seatgeek_events' table
    if c.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='seatgeek_events'"):
        size = c.fetchone()[0]
        page = size//25
    else:
        page = 0
    conn.close()
    '''

    # scrape seatgeek API into list of events:
    event_lst = get_seatgeek_data(post_code, mi_range, start_date, end_date)

    # parse through lst of dcts (event_lst) to create database from events lst:
    create_seatgeek_db(event_lst)

    # find nearest stop of each event in database, store in new table
    nearest_stop('AUonqD9X6H88AF1NldNupUd6ZtrTOx1e')

    # get resturant reccomendation based on specific budget closes to transit stop:
    # print("done")

    # generate_foo d

    # join both tables
    # calculate the distance between the transportation location and the event, add column to final  database
    join_databases()

    # take distance calculation + write them to a text file
    write_to_file()

main()


