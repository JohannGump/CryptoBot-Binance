import datetime
import requests
import json


def get_binance_data(pair, time):
    url = "https://data-api.binance.vision/api/v3/klines?symbol={pair}&interval={time}"
    response = requests.get(url.format(pair = pair, time = time))
    if response.status_code == 200:
        return response.json()
    else:
        print("Erreur lors de la requête :", response.status_code)
        return None
   

def append_data_to_file(data, filename):
    with open(filename, 'a') as file:
        json.dump(data, file)
        file.write('\n')


def timestamp_to_date(timestamp):
    # Convertir le timestamp en datetime et le formater en une nouvelle date
    timestamp_seconds = timestamp / 1000  # Convertir le timestamp en secondes
    datetime_obj = datetime.datetime.fromtimestamp(timestamp_seconds)
    date_str = datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
    return date_str