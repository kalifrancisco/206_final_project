from sqlite3.dbapi2 import Row
import matplotlib.pyplot as plt
import numpy as np
from numpy.lib.function_base import average
import requests
import re
import csv
import os
import sqlite3

# create dictionary
def big_dict():
    conn = sqlite3.connect('seatgeek_events.db')
    c = conn.cursor()

    c.execute("SELECT venue, distance, event_type, wheelchair_access, performer FROM joined_data")
    rows = c.fetchall()
    #print(rows)

    dct = {}

    for row in rows:
        #print(row)
        venue = row[0]
        dist = row[1]
        event_type = row[2]
        wheelchair = row[3]
        performer = row[4]

        dct[performer] = {"Venue": venue, "Distance": dist, "Event Type": event_type, "Wheelchair Access": wheelchair}

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



# visualization 3: average distance by event type, bar graph

def visual_3():
    # create new dictionary, event type as key, total distance as value
    conn = sqlite3.connect('seatgeek_events.db')
    cur = conn.cursor()
    info = cur.execute("SELECT distance, event_type FROM joined_data")
    rows = info.fetchall()

    event_type_dct = {} 

    for row in rows:
        if row[1] in event_type_dct.keys():
            event_type_dct[row[1]]["Total Distance"] += row[0]
            event_type_dct[row[1]]["Total Num"] += 1
        else:
            event_type_dct[row[1]] = {"Total Distance": row[0], "Total Num": 1}

        for key in event_type_dct.keys():
            avg_distance = event_type_dct[key]["Total Distance"] / event_type_dct[key]["Total Num"]
            event_type_dct[key]["Average Distance"] = avg_distance

    # print(event_type_dct)

    # NOW CREATE VISUALIZATION HERE USING THIS DICT

    keylst = []
    avgdistance = []

    for key in event_type_dct.keys():
        keylst.append(key)
        avgdistance.append(event_type_dct[key]["Average Distance"])


    first_font = {'family':'monospace','color':'black','size':10}
    second_font = {'family':'sans-serif','color':'gray','size':9}
    third_font = {'family':'sans-serif','color':'gray','size':9}

    plt.figure(figsize=(10,5))
    plt.bar(keylst, avgdistance, color=['red', 'orange', 'yellow'])
    plt.xlabel('Type of Show', fontdict=second_font)
    plt.ylabel('Average Distance (in degrees)', fontdict=third_font)
    plt.title('Average Distance to Public Transportation by Performance Type', fontdict=first_font)
    plt.show()
    plt.savefig("first-visual")

    return



def visual_4():
    conn = sqlite3.connect('seatgeek_events.db')
    cur = conn.cursor()
    info = cur.execute("SELECT distance, event_type FROM joined_data")
    rows = info.fetchall()
    
    event_type_dct = {} 

    for row in rows:
        if row[1] in event_type_dct.keys():
            event_type_dct[row[1]]["Total Distance"] += row[0]
            event_type_dct[row[1]]["Total Num"] += 1
        else:
            event_type_dct[row[1]] = {"Total Distance": row[0], "Total Num": 1}

        for key in event_type_dct.keys():
            avg_distance = event_type_dct[key]["Total Distance"] / event_type_dct[key]["Total Num"]
            event_type_dct[key]["Average Distance"] = avg_distance

    keylst = []
    totaldistance = []

    for key in event_type_dct.keys():
        keylst.append(key)
        totaldistance.append(event_type_dct[key]["Total Distance"])

    first_font = {'family':'monospace','color':'black','size':15}
    second_font = {'family':'sans-serif','color':'gray','size':3}

    plt.figure(figsize=(10,10))
    plt.title('Total Distance to different Types of Performances in NYC', fontdict=first_font)
    plt.xlabel('Type of Performance', fontdict=second_font)
    plt.pie(totaldistance, labels = keylst)
    plt.show() 


def main():

    dct = big_dict()
    visual_1(dct)
    visual_2(dct)
    visual_3()
    visual_4()

main()
