import requests
import json
import sqlite3
from bs4 import BeautifulSoup 
from requests import get, auth
from pprint import pprint
import math


# new API - using spotify && seatgeek apis:
    # client id: 6705c311c104b0f9032a0eb1ddd47d8
    # client secret: ff9e3ae8497b466199206d5aa2c637b1


# proj idea:
    # --> use Seatgeek api to get concert data for maybe give time period in a specific location
    # --> use Setlist api to get set list of given performers
    # --> [extra - maybe]: use Spotify api to generate playlist based on setlist

    # DATA REQUIREMENTS:
        # 1) Store at least 100 items (rows) in at least one table per API/website
        # 2) At least 1 API/website must have 2 tables (databases?) that share an integer key
        # 3) At least one database join used when selecting the data
        # 4) use SELECT from tables to calculate something


# SEATGEEK INFO:
    # client_id = "MjY1NDE4Mzd8MTY4MTk1NDUwMC44MDkzOTk2"
    # client_secret = "8e4c9d4ebe18b3fb44fe5b6c1c55c0993ac1efa46f92c0fc78520440a5c114af"


# all TODO:
    # 1) PLAN for seatgeek db
    # set geo location to get 100 items
    # store in first database
        # determine which integer key it should share w/ second data base TODO: (location_name will corresp with dist from train data)
    # plan for second database:
        # determine shared integer key
    # determine calcualtions
    # make visualizations

# this will be fine


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

    # pprint(raw_data_dct)

    # pprint(raw_data_dct["events"])

    # print("test dcts\n")
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
    for event in event_lst:
        #print(event)

        performer_name = event['performers'][0]['name']

        event_type = event['type']
        if '_' in event_type:
            event_type = event_type.replace('_', ' ')

        location_name = event["venue"]["name"]

        # log percise location data for transit api
        lat = event["venue"]["location"]["lat"]
        lon = event["venue"]["location"]["lon"]

        # insert data into table
        c.execute("INSERT INTO seatgeek_events VALUES (?, ?, ?, ?, ?)", (performer_name, event_type, location_name, lat, lon))

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

    stops_count = 0

    for row in rows:
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

        while stops_count < 100:
            headers = {"Api-Key": api_key}
            resp = requests.get(endpoint, headers=headers, params=params)

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

                c.execute("INSERT INTO transportation_data VALUES (?, ?, ?, ?, ?)", (stop_name, lat_c, lon_c, str(wheelchair), str(venue_name)))

                stops_count += 1
                # print("check sc2 ", stops_count)

            params['per_page'] = 100  # set per_page to 100 for subsequent requests

        if stops_count > 100:
            break

    conn.commit()
    conn.close()


def join_databases():

    conn1 = sqlite3.connect('seatgeek_events.db')
    c1 = conn1.cursor()
    conn2 = sqlite3.connect('transportation_data.db')
    c2 = conn2.cursor()

    # Create new table to store our combined data
    c1.execute('''CREATE TABLE IF NOT EXISTS joined_data
                 (performer TEXT, event_type TEXT, venue TEXT, latitude INTEGER, longitude INTEGER, stop_name TEXT, lat_cord INTEGER, lon_cord INTEGER, wheelchair_access TEXT)''')

    # if venue_name and venue are equal, store data together
    c1.execute('''SELECT seatgeek_events.performer, seatgeek_events.event_type, seatgeek_events.venue, seatgeek_events.latitude, seatgeek_events.longitude, transportation_data.stop_name, transportation_data.lat_cord, transportation_data.lon_cord, transportation_data.wheelchair_access
                  FROM seatgeek_events 
                  JOIN transportation_data 
                  ON seatgeek_events.venue = transportation_data.venue_name''')

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

        c1.execute("INSERT INTO joined_data VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (performer, event_type, venue, latitude, longitude, stop_name, lat_cord, lon_cord, wheelchair_access))

    conn1.commit()
    conn1.close()
    conn2.close()



def add_distance_column():

    conn = sqlite3.connect('joined_data.db')
    c = conn.cursor()

    # add new "distance" column to table
    c.execute("ALTER TABLE joined_data ADD COLUMN distance REAL")

    # access lat and long of both stop and venue
    c.execute("SELECT latitude, longitude, lat_cord, lon_cord FROM joined_data")
    rows = c.fetchall()

    for row in rows:
        
        #print(row)
        first = [row[0], row[1]]
        second = [row[2], row[3]]

        # calculate distance btwn points
        print(math.dist(first, second))

        distance = math.dist(first, second)

        # input distance into database
        c.execute("UPDATE joined_data SET distance = ? WHERE latitude = ? AND longitude = ?", (distance, row[0], row[1]))
        
    conn.commit()
    conn.close()

# write distance calculations for each venue to a new text file
def write_to_file():
    f = open("distance_calculations.txt", "w")

    conn = sqlite3.connect('joined_data.db')
    c = conn.cursor()

    c.execute("SELECT venue, stop_name, distance FROM joined_data")
    rows = c.fetchall()

    f.write("Venue", "Name of Stop", "Distance (in degrees)")
    for row in rows:
        f.write("Name of Venue: " + str(row[0]) + ", Name of Stop: " + str(row[1]) + ", Distance between: " + str(row[2]))
    
    f.close()

    return


# integrate closest resturant rec based on lat/lon of stop:
def generate_food_recs(api_key, budget):
    ep = 'https://api.yelp.com/v3/businesses/search'

    headers = {'Authorization': f'Bearer {api_key}'}
    params = {
        'term': 'restaurant',
        'latitude': 40.73735,
        'longitude': -73.99684,
        'radius': 1000,
        'price': budget,
        'sort_by': 'rating',
        'limit': 1
    }
    
    response = requests.get(ep, headers=headers, params=params)
    yelp_data = response.json()

    return yelp_data
    # print("try yelp\n", data)

    # restaurant = data['businesses'][0]

def main():

    # 1 - get lat + lon from seatgeek db (last two rows)
    # 2 - use that lat & lon using 'SELECT' to get lat and lon to ask transitland api about
    # 3 - add into transitland db w/ shared integer key
    # 4 - calculate something using distance and some data from transitland api
    # 5 - visualizations between concert location & bus stop (distance calculation)

    post_code = '10001'
    mi_range = '20mi'
    start_date = '2023-05-01'
    end_date = '2023-08-28'

    # scrape seatgeek API into list of events:
    event_lst = get_seatgeek_data(post_code, mi_range, start_date, end_date)

    # parse through lst of dcts (event_lst) to create database from events lst:
    create_seatgeek_db(event_lst)

    # find nearest stop of each event in database, store in new table
    nearest_stop('VG1wXRveWMAK73IfXT2XuUXs39Uby10R')

    # get resturant reccomendation based on specific budget closes to transit stop:
    print("baka")
    generate_food_recs('WRRtreepKK6FHXb9IHVirJ0ZolgQVE0xopdBsZAqNznG0LJ5i16faQGUEpBLzX2tLKj2oQstYbkbzre5HjXFU5xE2cwCmpY1pwnxJtASd1FbynJnnYxu_sJD7q5BZHYx', 2)

    # join both tables
    join_databases()

    # calculate the distance between the transportation location and the event, add column to final database
    add_distance_column()

    # take distance calculation + write them to a text file
    write_to_file()


main()







# —————————————————————————————————————————————————————————

# FOR LATER:
# Setlist.fm API endpoint
# setlistfm_url = 'https://api.setlist.fm/rest/1.0/search/setlists'

# # SeatGeek API parameters
# params = {
#     'q': 'Artist Name',
#     'geoip': '123.456.789.012', # User's IP address
#     'range': '10mi', # Distance from user's location
#     'datetime_utc.gte': '2023-05-01',
#     'datetime_utc.lte': '2023-06-01'
# }

# # Get concert data from SeatGeek API
# response = requests.get(seatgeek_url, params=params)
# concert_data = response.json()

# # Extract necessary data from concert data
# artist_name = concert_data['performers'][0]['name']
# event_name = concert_data['title']
# date = concert_data['datetime_utc']
# venue = concert_data['venue']['name']

# # Generate search query parameter for Setlist.fm API
# search_query = artist_name + ' ' + event_name
# event_name = 'concert'
# # Setlist.fm API parameters
# setlistfm_params = {
#     'artistName': "Nicki Minaj",
#     'p': 1, # Page number
#     'sort': 'relevance'
# }

# # Get setlist URL from Setlist.fm API
# setlist_fm_key = 'EvHhTr21yVmugWONkSNWnRqpD4SJKZOSd3o6'
# setlistfm_response = requests.get(setlistfm_url, params=setlistfm_params, headers={'x-api-key': setlist_fm_key})
# setlistfm_data = setlistfm_response.json()
# setlist_url = setlistfm_data['setlist'][0]['url']

# # Scrape data from setlist page using BeautifulSoup
# setlist_page = requests.get(setlist_url)
# setlist_soup = BeautifulSoup(setlist_page.content, 'html.parser')
# setlist_songs = setlist_soup.find_all('div', class_='songLabel')



# old create seatgeek:


# def create_seatgeek_db(event_lst):
#     # csv_dct = {}
#     performer_name = ""
#     event_type = ""
#     location_name = ""
#     # note: event['venue]['extended_address'] for 'Milwaukee, WI 53202'
#     # test_lst = [] #debug

#     # COLUMN IDEAS:
#         # event-type    performers    venue location
#     num_events = 1
#     print("numev:\n")
#     for event in event_lst:

#         print(num_events, "\n")
#         performer_name = event['performers'][0]['name']

#         event_type = event['type']
#         if '_' in event_type:
#                 event_type = event_type.replace('_', ' ')

#         location_name = event["venue"]["name"]

#         # test_lst.append(location_name) #debug
#         # num_events += 1 #debug


#     # return csv_dct


# OLD CHICAGO CTA IDEA:
# KAL HERE:
# tomorrow:
    # make function that calls the train api for each venue name (need to figure out how to get that code)
    # save that as a new table
    # join tables w/ JOIN && SELECT
    # create visualizations


# def get_cta_train_data(venue_name):
#     endpoint = "https://lapi.transitchicago.com/api/1.0/ttarrivals.aspx"
#     key = "YOUR_API_KEY"  # Replace with your API key
#     map_id = "YOUR_MAP_ID"  # Replace with the ID of the CTA map that covers the desired venue

#     # Define API parameters here
#     params = {
#         "key": key,
#         "mapid": map_id,
#         "max": 5  # Set maximum number of train arrivals to return
#     }

#     # Make API request and extract relevant information from response
#     response = requests.get(endpoint, params=params)
#     train_data = []
#     for train in response.json()["ctatt"]["eta"]:
#         if venue_name.lower() in train["destNm"].lower():
#             train_data.append({
#                 "train_line": train["rt"],
#                 "arrive_time": train["arrT"],
#                 "distance": train["isApp"]  # Distance in train stops
#             })

#     return train_data
