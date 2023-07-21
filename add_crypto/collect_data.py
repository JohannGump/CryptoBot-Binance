import requests
import json


def get_binance_data():
    url = "https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1h"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print("Erreur lors de la requête :", response.status_code)
        return None
    

def append_data_to_file(data, filename):
    with open(filename, 'a') as file:
        json.dump(data, file)
        file.write('\n')  # Ajoute une nouvelle ligne après chaque enregistrement


binance_data = get_binance_data()
filename = "/my_server/add_crypto/binance_data.json"

if binance_data is not None:
    # Ajout des données au fichier
    append_data_to_file(binance_data, filename)
    print("Données ajoutées au fichier :", filename)
else:
    print("Aucune donnée n'a été ajoutée au fichier.")
