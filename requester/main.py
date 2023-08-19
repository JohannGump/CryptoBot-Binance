import requests
from datetime import datetime, timedelta
import mysql.connector
from schemas import Symbol, TimeStep
import os
from dotenv import load_dotenv

#load variables from .env
load_dotenv()

#print version of dependencies
print("mysql.connector version:", mysql.connector.__version__)
print("requests version:", requests.__version__)

"""Requests Binance for Klines of the last 4 hours

    Parameters
    ----------
    symbol: String, 
        currency pair you want klines for
    start_time: int,
        period start, a timestamp in millis
    interval: enum = c("1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h",
    "1d", "3d", "1w", "1M")

"""

#Current time minus 4 'timestep unit'
def compute_start_time(interval: TimeStep, delta: int = 4):
    param = dict(zip(TimeStep, ['minutes', 'hours', 'days', 'weeks']))[interval]
    param = {param: delta}
    return int((datetime.now() - timedelta(**param)).timestamp()*1000)

def get_binance_last_klines(symbol: Symbol, interval: TimeStep, start_time: int):

    endpoint = "https://data-api.binance.vision/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval.value,
        "startTime": start_time
    }

    response = requests.get(endpoint, params=params)
    if response.status_code == 200:
        data = response.json()
    else:
        print("Erreur lors de la requête :", response.status_code)
        return None

    formatted_data = []
    for entry in data:
        open_time = datetime.fromtimestamp(entry[0] / 1000.0)
        open_price = float(entry[1])
        high_price = float(entry[2])
        low_price = float(entry[3])
        close_price = float(entry[4])
        volume = float(entry[5])

        formatted_data.append((symbol.name, interval.name, open_time, open_price, high_price, low_price, close_price, volume))

    return formatted_data

def check_duplicates(cursor, data):
    # Create a list to store records without duplicates
    unique_data = []

    # Check if the data already exists in the database based on symbol and open time
    select_query = "SELECT COUNT(*) FROM klines WHERE symbol = %s AND timestep = %s AND opentime = %s"

    for record in data:
        symbol, interval, open_time, *_ = record
        cursor.execute(select_query, (symbol, interval, open_time))
        result = cursor.fetchone()
        if result[0] == 0:
            # Data doesn't exist in the database, add to the list of unique_data
            unique_data.append(record)

    return unique_data

def insert_data_into_db(data):
    # Connection to database
    connection = mysql.connector.connect(
        host="db",
        user="root",
        password=os.environ.get('MYSQL_ROOT_PASSWORD_KLINES'),
        database=os.environ.get('MYSQL_DATABASE_KLINES'),
        port="3306"
    )

    # Create table if not exist
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS klines (
        Symbol enum({','.join([f"'{s.name}'" for s in Symbol])}) NOT NULL,
        TimeStep enum({','.join([f"'{t.name}'" for t in TimeStep])}) NOT NULL,
        OpenTime DATETIME NOT NULL,
        OpenPrice DOUBLE NOT NULL,
        HighPrice DOUBLE NOT NULL,
        LowPrice DOUBLE NOT NULL,
        ClosePrice DOUBLE NOT NULL,
        Volume DOUBLE NOT NULL,
        UNIQUE INDEX idx_open_time (Symbol, TimeStep, OpenTime)
    )
    """

    cursor = connection.cursor()

    cursor.execute(create_table_query)

    try:

        insert_query = "INSERT INTO klines (Symbol, TimeStep, OpenTime, OpenPrice, HighPrice, LowPrice, ClosePrice, Volume) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
         # Check for duplicates before inserting
        unique_data = check_duplicates(cursor, data)

        # Sort the unique data by symbol and open_time before insertion
        sorted_data = sorted(unique_data, key=lambda x: (x[0], x[1]))

        cursor.executemany(insert_query, sorted_data)
        connection.commit()
        print("Données insérées avec succès dans la base de données.")
    except Exception as e:
        print(f"Erreur lors de l'insertion des données: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    ts = os.getenv('TIMESTEP', TimeStep.HOURLY.name).upper()
    if ts not in TimeStep.__members__.keys():
        raise Exception(f"'{ts}' is not a valid timestep, please use one of {[t.name for t in TimeStep]}")

    ts = TimeStep[ts]
    start_time = compute_start_time(ts)
    for symbol in Symbol:
        binance_data = get_binance_last_klines(symbol, ts, start_time)
        insert_data_into_db(binance_data)