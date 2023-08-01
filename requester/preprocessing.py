import mysql.connector
import csv


def sort_klines_by_symbol_and_opentime():
    # Connection to database
    connection = mysql.connector.connect(
        host="db",
        user="root",
        password="password",
        database="klines_history",
        port="3306"
    )

    # Sort the klines table by symbol and opentime
    sort_query = """
            SELECT * FROM klines 
            WHERE opentime >= DATE_SUB((SELECT MAX(opentime) FROM klines), INTERVAL 3 HOUR)
            ORDER BY symbol, opentime;       
    """

    try:
        with connection.cursor() as cursor:
            cursor.execute(sort_query)
            data = cursor.fetchall()
            return data
    except Exception as e:
        print(f"Erreur lors du tri des données : {e}")
    finally:
        connection.close()

if __name__ == "__main__":

    data = sort_klines_by_symbol_and_opentime()

    # Write last 4 hours for each symbol to CSV file fit_data.csv
    file_path = "/app/data/fit_data.csv" 
    with open(file_path, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)

        # Write CSV header
        csv_writer.writerow(['symbol', 'opentime', 'open', 'high', 'low', 'close', 'volume'])

        print(data)

        # Write data to CSV
        for row in data:
            csv_writer.writerow(row)

    print("Le fichier fit_data.csv a été généré avec succès.")