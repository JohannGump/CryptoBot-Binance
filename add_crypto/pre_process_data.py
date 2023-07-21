import requests
import json
import pandas as pd
import datetime


def timestamp_to_date(timestamp):
    # Convertir le timestamp en datetime et le formater en une nouvelle date
    timestamp_seconds = timestamp / 1000  # Convertir le timestamp en secondes
    datetime_obj = datetime.datetime.fromtimestamp(timestamp_seconds)
    date_str = datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
    return date_str

filename = "/my_server/add_crypto/binance_data.json"
filename_preprocessed = "/my_server/add_crypto/binance_data_preprocessed.json"
df = pd.read_json(filename)
label = {
    0 : 'Open Time',    # Kline open time
    1 : 'Open Price',          # Open price
    2 : 'High Price',          # High price
    3 : 'Low Price',           # Low price
    4 : 'Close Price',         # Close price
    5 : 'Volume',              # Volume
    6 : 'Close Time',   # Kline Close time
    7 : 'Quote Asset Volume',  # Quote asset volume
    8 : 'Number Of Trades',      # Number of trades
    9 : 'Taker Buy Base',      # Taker buy base asset volume
    10 : 'Taker Buy Quote',     # Taker buy quote asset volume
    11 : 'Unused'                # Unused field, ignore
}


df = df.rename(label, axis = 1)
df['Open Time'] = df['Open Time'].apply(lambda x : timestamp_to_date(x))
df = df.set_index(df['Open Time'])
#df = df[['Close Price', 'High Price', 'Low Price', 'Open Price', 'Volume', 'Quote Asset Volume']]
df.to_csv(filename_preprocessed)

