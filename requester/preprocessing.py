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
        ORDER BY symbol, opentime
    """

    print('sort_klines_by_symbol_and_opentime')

    try:
        with connection.cursor() as cursor:
            cursor.execute(sort_query)
            sorted_data = cursor.fetchall()
            return sorted_data
    except Exception as e:
        print(f"Erreur lors du tri des données : {e}")
    finally:
        connection.close()

if __name__ == "__main__":

    sorted_data = sort_klines_by_symbol_and_opentime()

    # Generate dictionary to stock last 4 lines for each symbol
    last_4_rows_by_symbol = {}
    current_symbol = None
    row_count = 0

    for row in sorted_data:
        symbol, *_ = row

        # Check if symbol change or if if we arive to the last 4 lines of the current symbol
        if symbol != current_symbol or row_count == 4:
            current_symbol = symbol
            row_count = 0
            last_4_rows_by_symbol[symbol] = []

        last_4_rows_by_symbol[symbol].append(row)
        row_count += 1

    # Write last 4 lines for each symbol to CSV file fit_data.csv
    file_path = "/app/data/fit_data.csv" 
    with open(file_path, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)

        # Write CSV header
        csv_writer.writerow(['symbol', 'opentime', 'open', 'high', 'low', 'close', 'volume'])

        # Write data to CSV
        for symbol, rows in last_4_rows_by_symbol.items():
            for row in rows:
                csv_writer.writerow(row)

    print("Le fichier fit_data.csv a été généré avec succès.")