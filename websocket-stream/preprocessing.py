
# %%
import json
import datetime

### preprocessing des data: nettoyage
def modify_json_file(filename):
    with open(filename, 'r') as file:
        data = [json.loads(line) for line in file]
        
    # Parcourir chaque enregistrement dans le JSON
    data_new = []
    
    for record in data:
        # Vérifier si la clé "E" existe dans l'enregistrement
        if "E" in record:
            json_dict = json.loads(record) #transformation du string JSON en dict
            timestamp = json_dict["E"]
            date_str = timestamp_to_date(timestamp)
            json_dict["E"] = date_str
            data_new.append(json_dict)
        else:
            data_new.append(record)
        
    with open(filename, 'w') as file:
        json.dump(data_new, file)  # Réécrire le JSON modifié

def timestamp_to_date(timestamp):
    # Convertir le timestamp en datetime et le formater en une nouvelle date
    datetime_obj = datetime.datetime.fromtimestamp(timestamp / 1000)  # Diviser par 1000 pour convertir en secondes
    date_str = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
    return date_str


if __name__ == '__main__':

    modify_json_file('binance_data.json')

# %%