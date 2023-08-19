import mysql.connector
import csv
import os
from dotenv import load_dotenv
from schemas import TimeStep

#load variables from .env
load_dotenv()

def sort_klines_by_symbol_and_opentime(timestep: TimeStep):
    # Connection to database
    connection = mysql.connector.connect(
        host="db",
        user="root",
        password=os.environ.get('MYSQL_ROOT_PASSWORD_KLINES'),
        database=os.environ.get('MYSQL_DATABASE_KLINES'),
        port="3306"
    )

    # Sort the klines table by symbol and opentime
    unit = dict(zip(TimeStep, ['MINUTE', 'HOUR', 'DAY', 'WEEK']))[timestep]

    sort_query = f"""
    SELECT Symbol, OpenTime, OpenPrice, HighPrice, LowPrice, ClosePrice, Volume
    FROM klines
    WHERE opentime >= DATE_SUB((SELECT MAX(opentime) FROM klines WHERE TimeStep = %s), INTERVAL 3 {unit})
    AND TimeStep = %s
    ORDER BY symbol, opentime
    """

    try:
        with connection.cursor() as cursor:
            cursor.execute(sort_query, [timestep.name, timestep.name])
            data = cursor.fetchall()
            return data
    except Exception as e:
        print(f"Erreur lors du tri des données : {e}")
    finally:
        connection.close()

if __name__ == "__main__":

    ts = os.getenv('TIMESTEP', TimeStep.HOURLY.name).upper()
    if ts not in TimeStep.__members__.keys():
        raise Exception(f"'{ts}' is not a valid timestep, please use one of {[t.name for t in TimeStep]}")
    
    data = sort_klines_by_symbol_and_opentime(TimeStep[ts])

    # Write last 4 hours for each symbol to CSV file fit_data.csv
    file_path = f"/app/data/fit_data_{ts}.csv"
    with open(file_path, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)

        # Write CSV header
        csv_writer.writerow(['symbol', 'opentime', 'open', 'high', 'low', 'close', 'volume'])

        print(data)

        # Write data to CSV
        for row in data:
            csv_writer.writerow(row)

    print("Le fichier fit_data.csv a été généré avec succès.")