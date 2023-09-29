from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
import datetime
import mysql.connector
import os

my_dag = DAG(
    dag_id='test_crypto_bot_dag',
    description='test_crypto_bot_dag',
    tags=['CryptoBot'],
    schedule_interval=None,
    default_args={
        'owner': 'airflow',
        'start_date': days_ago(2),
    }
)


klin_conn = {
    'host': os.getenv('MYSQL_HOST_PREDICTIONS'), #db in prod
    'user': os.getenv('MYSQL_USER_PREDICTIONS'),
    'password': os.getenv('MYSQL_PASSWORD_PREDICTIONS'),
    'database': os.getenv('MYSQL_DATABASE_PREDICTIONS'),
    'port': "3306",
    'auth_plugin': 'mysql_native_password'
}

# definition of the function to execute
def print_data():
    print('debut de la fonction')
    connexion = mysql.connector.connect(**klin_conn)
    curseur = connexion.cursor()
    nom_de_la_table = 'klines'
    requete_sql = f"SELECT * FROM {nom_de_la_table}"

    curseur.execute(requete_sql)
    resultats = curseur.fetchall()
    curseur.close()
    connexion.close()

    print(requete_sql)

    for ligne in resultats:
        print(ligne)




my_task = PythonOperator(
    task_id='my_very_first_task',
    python_callable=print_data,
    dag=my_dag
)

