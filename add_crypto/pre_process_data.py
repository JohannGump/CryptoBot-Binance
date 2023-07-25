import requests
import json
import pandas as pd
import os

import configuration
from custo_functions import *


#---variable
pairs = configuration.pairs
label = configuration.label
data_JSON_folder = configuration.data_JSON_folder
filename_JSON = configuration.filename_JSON
volume_folder = configuration.volume_folder
filename_preprocessed = configuration.filename_preprocessed



for pair in pairs:
    #read JSON datas and create a dataframe
    df = pd.read_json(filename_JSON.format(pair=pair))

    #rename column names
    df = df.rename(label, axis = 1)

    #change date format
    df['Open Time'] = df['Open Time'].apply(lambda x : timestamp_to_date(x))

    #set the date column as index
    df = df.set_index(df['Open Time'])

    #choose the features
    #df = df[['Close Price', 'High Price', 'Low Price', 'Open Price', 'Volume', 'Quote Asset Volume']]

    #save data in the CSV file
    df.to_csv(filename_preprocessed.format(pair=pair))

    #delete the JSON file
    os.remove(filename_JSON.format(pair=pair))

