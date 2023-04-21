from sqlite3.dbapi2 import Row
from bs4 import BeautifulSoup
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

    conn = sqlite3.connect('joined_data.db')
    cur = conn.cursor()

    info = cur.execute("SELECT venue, distance, event_type, wheelchair_access, performer FROM joined_data")
    rows = info.fetchall()

    dct = {}

    for row in rows:
        print(row)
        venue = row[0]
        dist = row[1]
        event_type = row[2]
        wheelchair = row[3]
        performer = row[4]

        dct[performer] = {"Venue": venue, "Distance": dist, "Event Type": event_type, "Wheelchair Access": wheelchair}


# visualization 1: top 10 farthest distances
def visual_1(newdct):
    return


# visualization 2: top 10 closes distances
def visual_2(newdct):
    return


# visualization 3: average distance by event type, bar graph
def visual_3():

    # create new dictionary, event type as key, total distance as value
    conn = sqlite3.connect('joined_data.db')
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

    # NOW CREATE VISUALIZATION HERE USING THIS DICT
    
    return



def main():
    big_dict = big_dict()

    visual_1(big_dict)
    visual_2(big_dict)
    visual_3()


main()