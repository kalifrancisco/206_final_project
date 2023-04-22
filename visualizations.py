from sqlite3.dbapi2 import Row
import matplotlib.pyplot as plt
import numpy as np
from numpy.lib.function_base import average
import requests
import re
import csv
import os
import sqlite3
from math import radians, cos, sin, sqrt, asin
import matplotlib.colors as mcolors


# create dictionary
def big_dict():
    conn = sqlite3.connect('seatgeek_events.db')
    c = conn.cursor()

    c.execute("SELECT venue, transit_distance, wheelchair_access, performer FROM joined_data")
    rows = c.fetchall()
    #print(rows)

    dct = {}

    for row in rows:
        #print(row)
        venue = row[0]
        dist = row[1]
        # event_type = row[2]
        wheelchair = row[2]
        performer = row[3]

        dct[performer] = {"Venue": venue, "Distance": dist, "Wheelchair Access": wheelchair}

    return dct

# visualization 1: Distances

def visual_1(dct):
    performers = dct.keys()
    distances = []

    for performer in performers: 
        distances.append(dct[performer]["Distance"])

    first_font = {'family':'Times New Roman','color':'black','size':20}
    second_font = {'family':'arial','color':'gray','size':7}
    third_font = {'family':'arial','color':'gray','size':14}
    
    # print(performers)
    # print(distances)

    plt.figure(figsize=(16,8))
    plt.bar(performers, distances, color=['pink'])
    plt.xlabel('Performer', fontdict=second_font)
    plt.ylabel('Distance (in degrees)', fontdict=third_font)
    plt.title('Distance to Public Transportation by Performer', fontdict=first_font)
    plt.xticks(rotation=90)
    plt.show()

    plt.savefig("first-visual")



def addlabels(x,y):
    for i in range(len(x)):
        plt.text(i, y[i]//2, y[i], ha = 'center')


# visualization 2: top 10 closest distances
def visual_2(newdct):

    performers = newdct.keys()
    distances = []
    for performer in performers: 
        distances.append(newdct[performer]["Distance"])

    performers = list(performers)    
    newlst = []
    #print(performers)



    for index in range(0,len(performers)):
        #print(performers)
        #print(distances)
        newlst.append((performers[index], distances[index]))

    sorted_lst = sorted(newlst, key=lambda x: x[1])
    sorted_lst = sorted_lst[:10]
    # print(sorted_lst)

    lst1 = []
    lst2 = []


    for item in sorted_lst:
        lst1.append(item[0])
        lst2.append(item[1])


    first_font = {'family':'Times New Roman','color':'black','size':20}
    second_font = {'family':'arial','color':'gray','size':7}
    third_font = {'family':'arial','color':'gray','size':14}

    # this isn't working rn but i'm trying to put the exact distance on each bar
    addlabels(lst1, lst2)

    plt.figure(figsize=(8,8))
    plt.bar(lst1, lst2, color=['purple'])
    plt.xlabel('Performer', fontdict=second_font)
    plt.ylabel('Distance (in degrees)', fontdict=third_font)
    plt.xticks(rotation=90)
    plt.title('Top 10 Closest Performances to Public Transportation in NYC', fontdict=first_font)
    plt.show()
    plt.savefig("first-visual")


def rest_dict_1():

    conn = sqlite3.connect('seatgeek_events.db')
    c = conn.cursor()
    c.execute("SELECT stop_name, transit_distance, restaurant_distance FROM joined_data")

    rows = c.fetchall()
    #print(rows)
    dct = {}
    # create dict w/ venue and distance from nearest resturant from transit stop
    for row in rows:
        #print(row)
        stop = row[0]
        t_dist = row[1]
        r_dist = row[2]
        dct[stop] = {"Distance from nearest restaurant": abs(t_dist - r_dist)}
    return dct


def vis_3():
    data_dict = rest_dict_1()

    # Extract the stop names and distances from the data_dict
    stops = list(data_dict.keys())
    distances = [data_dict[stop]["Distance from nearest restaurant"] for stop in stops]

    stops, distances = zip(*sorted(zip(stops, distances), key=lambda x: x[1]))

    fig, ax = plt.subplots()

    colors = ['teal' if dist < 500 else 'darkslategray' for dist in distances] 
    ax.barh(stops, distances, color=colors)  # set colors
    ax.set_xlabel('Distance from 10 Closest Transit Stops to Nearest Restaurant', fontdict={'family':'monospace','color':'black','size':10})
    ax.set_ylabel('Transit Stop', fontdict={'family':'monospace','color':'black','size':10})
    ax.set_title('Distance from 10 Closest Transit Stops to Nearest Restaurant by Transit Stop', fontdict={'family':'monospace','color':'black','size':12})


    plt.show()

def rest_dict_all():
    conn = sqlite3.connect('seatgeek_events.db')
    c = conn.cursor()
    c.execute("SELECT stop_name, transit_distance, restaurant_distance FROM joined_data")

    rows = c.fetchall()
    dct = {}
    for row in rows:
        stop = row[0]
        t_dist = row[1]
        r_dist = row[2]
        dct[stop] = {"Distance from nearest restaurant": abs(t_dist - r_dist)}
    return dct

def vis_4():


    data_dict = rest_dict_all()

    stops = list(data_dict.keys())
    distances = [data_dict[stop]["Distance from nearest restaurant"] for stop in stops]

    fig, ax = plt.subplots()
    colors = ['#DEA5A4' if dist < 500 else 'darkslategray' for dist in distances]
    ax.scatter(distances, stops, color=colors, alpha=0.8)
    ax.set_xlabel('Distance from 10 Closest Transit Stops to Nearest Restaurant', fontdict={'family':'monospace','color':'black','size':10})
    ax.set_ylabel('Transit Stop', fontdict={'family':'monospace','color':'black','size':10})
    ax.set_title('Distance from Transit Stops to Nearest Restaurant', fontdict={'family':'monospace','color':'black','size':12})

    plt.show()


def main():

    dct = big_dict()
    visual_1(dct)
    visual_2(dct)
    # visual_3()
    # visual_4()

    vis_3()
    vis_4()

main()
