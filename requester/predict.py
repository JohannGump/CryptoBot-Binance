import pandas as pd
import requests
import json
from schemas import Symbol
import sqlalchemy
from sqlalchemy import create_engine
import mysql.connector
import os
from dotenv import load_dotenv
import datetime
import pytz

#load variables from .env
load_dotenv()


#print version of dependencies
print("SQLAlchemy version:", sqlalchemy.__version__)
print("mysql.connector version:", mysql.connector.__version__)
print("requests version:", requests.__version__)

def get_predictions_and_save_in_database():
    # Charger les données depuis le fichier CSV
    df = pd.read_csv('/app/data/fit_data.csv')

    # Supprimer les colonnes 'id', 'symbol' et 'opentime'
    df = df.drop(columns=['id', 'symbol', 'opentime'])

    # Convertir les données en liste de listes
    data_list = df.values.tolist()

    # Ajouter une dimension supplémentaire
    data_list = [data_list]

    API = "http://c-predict:8501/v1/models/hourly:predict"
    JSON = json.dumps({"instances": data_list})

    response = requests.post(API, data=JSON)

    if response.status_code == 200:
        data = response.json()
        print(data)
    else:
        print("Error:", response.status_code, response.text)

    # Obtenir la date et l'heure actuelles en temps universel
    current_utc_time = datetime.datetime.now(pytz.utc)

    # Définir un DataFrame avec les symboles et les prédictions triées par ordre alphabétique
    sorted_columns = sorted([symbol.name for symbol in Symbol])
    df = pd.DataFrame(data['predictions'], columns=sorted_columns)

    # Ajouter la date en tant que colonne dans le DataFrame
    df['Datetime'] = current_utc_time

    print(df.head())

    # Inscrire les prédictions dans la base de données
    connection_params = {
        "host": "db_predict",
        "user": "root",
        "password": os.environ.get('MYSQL_ROOT_PASSWORD_PREDICTIONS'),
        "database": os.environ.get('MYSQL_DATABASE_PREDICTIONS'),
        "port": "3306"
    }

    # Se connecter à la base de données
    connection = mysql.connector.connect(**connection_params)

    # Créer un moteur SQLAlchemy à partir de la connexion MySQL
    engine = create_engine('mysql+mysqlconnector://' + connection_params["user"] + ':' + connection_params["password"]
                        + '@' + connection_params["host"] + ':' + connection_params["port"] + '/'
                        + connection_params["database"])

    # Insérer les prédictions dans la table "predictions"
    df.to_sql(con=engine, name="predictions", if_exists="append", index=False)

    # Fermer la connexion
    connection.close()

if __name__ == "__main__":
    get_predictions_and_save_in_database()