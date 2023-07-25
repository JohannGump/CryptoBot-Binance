import requests
import json
import os

import configuration
from custo_functions import *


pip_time = configuration.pip_time
data_JSON_folder = configuration.data_JSON_folder
filename_JSON = configuration.filename_JSON
pairs = configuration.pairs


for pair in pairs:
    binance_data = get_binance_data(pair, pip_time)    
    if binance_data is not None:
        # Ajout des données au fichier
        append_data_to_file(binance_data, filename_JSON.format(pair = pair))
    else:
        print("Aucune donnée n'a été ajoutée au fichier.")
