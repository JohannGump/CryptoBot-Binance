import pandas as pd
import requests
import json
from schemas import Symbol, TimeStep
import sqlalchemy
from sqlalchemy import create_engine
import mysql.connector
import os
import datetime
import pytz
import logging

logging.basicConfig(format='[%(asctime)s] [%(levelname)s] %(module)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

connection_params = {
    "host": os.getenv('MYSQL_HOST_PREDICTIONS'),
    "user": os.getenv('MYSQL_USER_PREDICTIONS'),
    "password": os.getenv('MYSQL_PASSWORD_PREDICTIONS'),
    "database": os.getenv('MYSQL_DATABASE_PREDICTIONS'), 
    "port": "3306"
}

PREDICT_SERVER_HOST=os.getenv('PREDICT_SERVER_HOST')

def get_predictions_and_save_in_database(timestep: TimeStep):
    # Charger les données depuis le fichier CSV
    df = pd.read_csv(f'/app/data/fit_data_{timestep.name}.csv')

    # Dernières lignes de chaque sequence (pour calcul du prix et date prédite)
    seq_lasts = df[3::4].set_index('symbol')

    # Supprimer les colonnes 'id', 'symbol' et 'opentime'
    df = df.drop(columns=['symbol', 'opentime'])

    # Convertir les données en liste de listes
    data_list = df.values.tolist()

    # Ajouter une dimension supplémentaire
    data_list = [data_list]

    API = f"http://{PREDICT_SERVER_HOST}/v1/models/{timestep.name.lower()}:predict"
    JSON = json.dumps({"instances": data_list})

    response = requests.post(API, data=JSON)

    if response.status_code == 200:
        data = response.json()
    else:
        logging.error(f"{timestep.name} predictions error {response.text}")
        exit(1)

    # Obtenir la date et l'heure actuelles en temps universel
    current_utc_time = datetime.datetime.now(pytz.utc)

    # Définir un DataFrame avec les symboles et les prédictions triées par ordre alphabétique
    sorted_columns = sorted([symbol.name for symbol in Symbol])
    df = pd.DataFrame(data['predictions'], columns=sorted_columns)

    # On prend la transposée (symbols en tant qu'index) et on ajoute les
    # champs nécéssaires (cf. schéma `ensure_predictions_table`)
    df = df.T.rename_axis('symbol').rename(columns={0: 'PctChange'})
    df['InTime'] = current_utc_time
    unit = dict(zip(TimeStep, ('T', 'H', 'D', 'W')))[timestep]
    df['OpenTime'] = seq_lasts['opentime'].astype('datetime64[ns]') + pd.Timedelta(4, unit=unit)
    df['TimeStep'] = timestep.name
    df['ClosePrice'] = seq_lasts['close'] * df['PctChange']
    df = df.reset_index()

    # Se connecter à la base de données
    connection = mysql.connector.connect(**connection_params)

    # Créer un moteur SQLAlchemy à partir de la connexion MySQL
    engine = create_engine('mysql+mysqlconnector://' + connection_params["user"] + ':' + connection_params["password"]
                        + '@' + connection_params["host"] + ':' + connection_params["port"] + '/'
                        + connection_params["database"])

    # Insérer les prédictions dans la table "predictions"
    try:
        df.to_sql(con=engine, name="predictions", if_exists="append", index=False)
        logging.info(f"{df.iloc[0].TimeStep} predictions inserted for {df.iloc[0].OpenTime}")
    except sqlalchemy.exc.IntegrityError:
        logging.info(f"{df.iloc[0].TimeStep} predictions already exists for {df.iloc[0].OpenTime}")

    # Fermer la connexion
    connection.close()

def ensure_predictions_table():
    """Create MySQL predictions schema if needed."""
    cnx = mysql.connector.connect(**connection_params)
    cursor = cnx.cursor()
    query = f"""
    CREATE TABLE IF NOT EXISTS predictions (
        Symbol enum({','.join([f"'{s.name}'" for s in Symbol])}) NOT NULL,
        TimeStep enum({','.join([f"'{t.name}'" for t in TimeStep])}) NOT NULL,
        InTime DATETIME NOT NULL,
        OpenTime DATETIME NOT NULL,
        PctChange DOUBLE NOT NULL,
        ClosePrice DOUBLE NOT NULL,
        UNIQUE INDEX idx_predictions_sto (Symbol, TimeStep, OpenTime)
    )
    """
    cursor.execute(query)
    cursor.close()
    cnx.close()

if __name__ == "__main__":
    ts = os.getenv('TIMESTEP', TimeStep.HOURLY.name).upper()
    if ts not in TimeStep.__members__.keys():
        logging.error(f"'{ts}' is not a valid timestep, please use one of {[t.name for t in TimeStep]}")
        exit(1)

    ensure_predictions_table()
    get_predictions_and_save_in_database(TimeStep[ts])