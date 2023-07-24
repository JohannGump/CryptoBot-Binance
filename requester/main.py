import requests
from datetime import datetime, timedelta
import mysql.connector
from schemas import Symbol

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

#Current time less 4 hours
START_TIME = int((datetime.now() - timedelta(hours=4)).timestamp()*1000)

def get_binance_last_klines(symbol: Symbol, interval = "15m", start_time = START_TIME):

    endpoint = "https://data-api.binance.vision/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
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

        formatted_data.append((symbol, open_time, open_price, high_price, low_price, close_price, volume))

    return formatted_data

def insert_data_into_db(data):
    # Connection to database
    connection = mysql.connector.connect(
        host="db",
        user="root",
        password="password",
        database="klines_history",
        port="3306"
    )

    # Create table if not exist
    create_table_query = """
    CREATE TABLE IF NOT EXISTS klines (
        id INT AUTO_INCREMENT PRIMARY KEY,
        symbol varchar(255),
        opentime DATETIME,
        open FLOAT,
        high FLOAT,
        low FLOAT,
        close FLOAT,
        volume FLOAT
    );
    """

    cursor = connection.cursor()

    cursor.execute(create_table_query)

    insert_query = "INSERT INTO klines (symbol, opentime, open, high, low, close, volume) VALUES (%s, %s, %s, %s, %s, %s, %s)"

    try:
        cursor.executemany(insert_query, data)
        connection.commit()
        print("Données insérées avec succès dans la base de données.")
    except Exception as e:
        print(f"Erreur lors de l'insertion des données: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    for symbol in Symbol:
        binance_data = get_binance_last_klines(symbol)
        insert_data_into_db(binance_data)