import requests
import json


pairs = ['ADAUSDT', 
         'BTCUSDT', 
         'BNBUSDT', 
         'ETHUSDT', 
         'XRPUSDT']

def get_binance_data(pair, time):
    url = "https://data-api.binance.vision/api/v3/klines?symbol={pair}&interval={time}"
    response = requests.get(url.format(pair = pair, time = time))
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

for pair in pairs:
    binance_data = get_binance_data(pair, '1h')

    filename = "/src/add_crypto/{pair}_binance_data.json"


    if binance_data is not None:
        # Ajout des données au fichier
        append_data_to_file(binance_data, filename.format(pair = pair))
    else:
        print("Aucune donnée n'a été ajoutée au fichier.")
