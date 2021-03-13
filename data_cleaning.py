# -*- coding: utf-8 -*-
"""
Created on Thu Mar  4 18:02:27 2021

@author: tzwn
"""

import pandas as pd
import numpy as np
import re

CSV_PATH = "data/"
GNAF_PATH = "GNAF/"

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 0)

suburbs = {"Perth, WA": 6000, 
           "East Perth, WA": 6004, 
           "Northbridge, WA": 6003,
           "Nedlands, WA": 6009, 
           "Crawley, WA": 6009, 
           "West Perth, WA": 6005,
           "Doubleview, WA": 6018, 
           "Innaloo, WA": 6018}

suburb_dfs = [pd.read_csv("{}{}.csv".format(CSV_PATH, suburb)) for suburb in suburbs.keys()]

df = pd.concat(suburb_dfs)

df["Postcode"] = df.Suburb.apply(lambda x: suburbs[x])

longlat = pd.read_csv("{}address_longlat.csv".format(GNAF_PATH))

longlat["IN_SUBURB"] = longlat.POSTCODE.apply(lambda x: 1 if x in suburbs.values() else 0)

longlat = longlat.loc[longlat.IN_SUBURB==1]

longlat.columns

for i in df.Address:
    if "sold" in i.lower():
        print(i)
# clean address
df.Address = df.Address.apply(lambda x: x.replace("Apartment", '').replace("Apt.", '') if "Ap" in str(x) else x)
df.Address = df.Address.apply(lambda x: x.replace("SOLD-SOLD", '').replace("SOLD", '').replace("Perth", '').strip().upper())
df.Address = df.Address.apply(lambda x: x.replace(" L", " LANE").strip() if re.search(r"( L)$", x) else x)

# street names
df["street_names"] = df.Address.apply(lambda x: ' '.join(re.findall(r"([A-Z]{2,})+", x)))

df["Address_number"] = df.apply(lambda x: re.match(r"(.*) {}$".format(x["street_names"]), x["Address"]), axis=1)

tmp = []

for i, obj in enumerate(df.Address_number):
    if obj==None:
        tmp.append(i)

df[["Address", "street_names"]].iloc[tmp]

df.loc[df.street_names.apply(lambda x: True if "OF" in x else False)]

df.street_names = df.street_names.apply(lambda x: x.replace("LOT OF ", '').replace("LOT", '').replace(" AND ", '').replace("QIII", '').strip())

df.street_names = df.street_names.apply(lambda x: x.replace("AND", '').strip() if re.match(r"^AND ", x) else x)

df.street_names = df.street_names.apply(lambda x: x.replace("AND", '').strip() if re.match(r"^AND ", x) else x)

df.street_names = df.street_names.apply(lambda x: x.replace("AB ", '').strip() if re.match(r"^AB ", x) else x)


# Address numbers
df["Address_number"] = df.apply(lambda x: re.match(r"(.*) {}$".format(x["street_names"]), x["Address"]), axis=1)

tmp = []

for i, obj in enumerate(df.Address_number):
    if obj==None:
        tmp.append(i)

df[["Address", "street_names"]].iloc[tmp]

df["Address_number"] = df.apply(lambda x: re.match(r"(.*) {}$".format(x["street_names"]), x["Address"]).groups()[0], axis=1)


# Street type code
df["STREET_TYPE_CODE"] = df.street_names.apply(lambda x: np.nan if len(x.split())==1 else x.split()[-1])

df.STREET_TYPE_CODE.unique()

df["STREET_NAME"] = df.street_names.apply(lambda x: x if len(x.split())==1 else ' '.join(x.split()[:-1]))

# street numbers
df.Address_number.unique()

df.loc[df.Address_number.apply(lambda x: re.search(r"\d+[A-Z]?$",x)).apply(lambda x: True if x==None else False)]
# just get the numbers
df["Address_number_only"] = df.Address_number.apply(lambda x: re.sub(r"[A-Z]", '', x))

df.loc[df.Address_number_only.apply(lambda x: True if '-' in x else False)]
df.loc[df.Address_number_only.apply(lambda x: True if ',' in x else False)]

df["NUMBER"] = df.Address_number_only.apply(lambda x: str(x).split('/')[1].strip() if '/' in str(x) else x)
df["FLAT_NUMBER"] = df.Address_number_only.apply(lambda x: str(x).split('/')[0].strip() if '/' in str(x) else np.nan)

df["NUMBER_FIRST"] = df.NUMBER.apply(lambda x: str(x).split('-')[0].strip() if '-' in str(x) else x)
df["NUMBER_LAST"] = df.NUMBER.apply(lambda x: str(x).split('-')[1].strip() if '-' in str(x) else np.nan)

df["FLAT_FIRST"] = df.FLAT_NUMBER.apply(lambda x: str(x).split('-')[0].strip() if '-' in str(x) else x)
df["FLAT_LAST"] = df.FLAT_NUMBER.apply(lambda x: str(x).split('-')[1].strip() if '-' in str(x) else np.nan)

df.NUMBER_FIRST = df.NUMBER_FIRST.apply(lambda x: re.match(r"(\d+)?(\D+)?(\d+)", x).groups()[-1] if ' ' in x else x)

##tmp = df[["NUMBER_FIRST", "NUMBER_LAST", "FLAT_FIRST", "FLAT_LAST", "STREET_TYPE_CODE", "STREET_NAME", "Address"]]

# todo better join/match
def join_address(x):
    col_order = ['NUMBER_FIRST', 'STREET_NAME', 'STREET_TYPE_CODE']
    l = [str(x[col]).upper().replace('.0','') +' ' if pd.notna(x[col]) else '' for col in col_order]
    return ''.join(l).strip()

longlat["ADDR"] = longlat.apply(join_address,axis=1)
small_longlat = longlat.drop_duplicates(subset=["ADDR"])

df["ADDR"] = df.apply(join_address, axis=1)

df = df.set_index("ADDR").join(small_longlat[["ADDR", "LONGITUDE", "LATITUDE"]].set_index("ADDR"), rsuffix="_longlat")

df["ADDR"] = df.index

df = df.set_index("index").reset_index()

df = df.drop(["street_names", "Address_number", "Address_number_only", "NUMBER"], axis=1)


df.isna().sum()

df.loc[pd.isna(df.LONGITUDE), ["NUMBER_FIRST", "ADDR", "Address"]]

# distance
distances = []
for distance in df.Distance:
    if pd.isna(distance):
        distances.append(distance)
    elif "km" in distance:
        distances.append(float(re.match(r"([0-9\.]+) km to CBD", distance).groups()[0]) * 1000)
    elif "metres" in distance:
        distances.append(float(re.match(r"([0-9]+) metres to CBD", distance).groups()[0]))
    else:
        distances.append(distance)

df["CBD_distance_m"] = distances

# transport
transports = []
for transport in df.Transport:    
    if pd.isna(transport):
        transports.append(transport)
    elif "km" in transport:
        transports.append(float(re.match(r"([0-9\.]+) km to .*", transport).groups()[0]) * 1000)
    elif "metres" in transport:
        transports.append(float(re.match(r"([0-9]+) metres to .*", transport).groups()[0]))
    else:
        transports.append(transport)
        
df["Closest_station_m"] = transports

# sold times
from datetime import datetime

Sold_dates = []
Rent_dates = []
Last_Sold_dates = []

for i, date in enumerate(df.Sold_Date):
    if pd.notna(date):        
        date = ' '.join(re.findall(r"(\d+ )?(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\s?(\d+)", date)[0]).strip()        
        if len(date.split()) == 2:
            Sold_dates.append(datetime.strptime(date, "%b %Y").timestamp())
        elif len(date.split()) == 3:
            Sold_dates.append(datetime.strptime(date, "%d %b %Y").timestamp())
        else:
            Sold_dates.append(datetime.strptime(date, "%Y").timestamp())
    else:
        Sold_dates.append(date)
        
for i, date in enumerate(df.Rent_Date):
    if pd.notna(date):
        date = ' '.join(re.findall(r"(\d+ )?(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\s?(\d+)", date)[0]).strip()        
        if len(date.split()) == 2:
            Rent_dates.append(datetime.strptime(date, "%b %Y").timestamp())
        elif len(date.split()) == 3:
            Rent_dates.append(datetime.strptime(date, "%d %b %Y").timestamp())
        else:
            Rent_dates.append(datetime.strptime(date, "%Y").timestamp())
    else:
        Rent_dates.append(date)
        
for i, date in enumerate(df.Last_Sold_Date):
    if pd.notna(date):
        date = ' '.join(re.findall(r"(\d+ )?(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\s?(\d+)", date)[0]).strip()        
        if len(date.split()) == 2:
            Last_Sold_dates.append(datetime.strptime(date, "%b %Y").timestamp())
        elif len(date.split()) == 3:
            Last_Sold_dates.append(datetime.strptime(date, "%d %b %Y").timestamp())
        else:
            Last_Sold_dates.append(datetime.strptime(date, "%Y").timestamp())
    else:
        Last_Sold_dates.append(date)
        
df["Sold_timestamp"] = Sold_dates
df["Rent_timestamp"] = Rent_dates
df["Last_Sold_timestamp"] = Last_Sold_dates

df["Sold_Date_diff"] = df.Sold_timestamp - df.Last_Sold_timestamp

df.dtypes

df.columns

df = df.drop(["index", "Unnamed: 0", "Retirement_Living", "Residential", "Villa", "Block_Of", "Land"], axis = 1)

df["Suburb_state"] = df.Suburb
df.Suburb = df.Suburb_state.apply(lambda x: x.split(', ')[0].upper())
df["State"] = df.Suburb_state.apply(lambda x: x.split(', ')[1].upper())


suburbs_of_interest = {"Perth, WA": 6000, 
                       "East Perth, WA": 6004, 
                       "Northbridge, WA": 6003,
                       "Nedlands, WA": 6009, 
                       "Crawley, WA": 6009, 
                       "West Perth, WA": 6005}


#df = df.loc[df.Suburb.apply(lambda x: x in [sub.upper() for sub in suburbs_of_interest.keys()])]

df.to_csv("{}Perth_Housing.csv".format(CSV_PATH))


