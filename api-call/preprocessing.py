# %%

import json
import datetime

def modify_json_file(filename):
    with open(filename, 'r') as file:
        data = json.load(file)  # Charger le contenu JSON existant

    # Modifier la date dans chaque enregistrement
    for record in data:
        timestamp = record[0]
        # Modifier la valeur de la date selon vos besoins
        # Par exemple, convertir le timestamp en datetime et le formater en une nouvelle date
        # Ici, nous utilisons le format "%Y-%m-%d %H:%M:%S"
        date_str = timestamp_to_date(timestamp)
        record[0] = date_str

    with open(filename, 'w') as file:
        json.dump(data, file)  # Réécrire le JSON modifié

def timestamp_to_date(timestamp):
    # Convertir le timestamp en datetime et le formater en une nouvelle date
    timestamp_seconds = timestamp / 1000  # Convertir le timestamp en secondes
    datetime_obj = datetime.datetime.fromtimestamp(timestamp_seconds)
    date_str = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
    return date_str

# Utilisation du script
filename = "binance_data.json"

# Modifier la date dans le JSON du fichier
modify_json_file(filename)
print("Les dates dans le fichier JSON ont été modifiées.")

# %%