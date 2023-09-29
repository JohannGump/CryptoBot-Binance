from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
import datetime
import pandas as pd
import mysql.connector

my_dag = DAG(
    dag_id='check_precision_dag',
    description='check_precision_dag',
    tags=['CryptoBot'],
    schedule_interval=None,
    default_args={
        'owner': 'airflow',
        'start_date': days_ago(2),
    }
)


klin_conn = {
    'host': 'db', #db in prod
    'user': 'root',
    'password': 'password',
    'database': 'klines_history',
    'port': "3306",
    'auth_plugin': 'mysql_native_password'
}
predict_conn = {
    'host': 'db', #db in prod
    'user': 'root',
    'password': 'password',
    'database': 'klines_history',
    'port': "3306",
    'auth_plugin': 'mysql_native_password'
}


def sql_to_df(connector, table):    
    connexion = mysql.connector.connect(**connector)
    curseur = connexion.cursor()
    requete_sql = f"SELECT * FROM {table}"
    curseur.execute(requete_sql)
    dataframe = pd.DataFrame(curseur.fetchall(), columns=curseur.column_names)
    curseur.close()
    connexion.close()
    return dataframe

def get_result():
    df_klines = sql_to_df(klin_conn, 'klines')
    df_predictions = sql_to_df(klin_conn, 'predictions')

    df_work = df_predictions.merge(right = df_klines, on = ['Symbol', 'TimeStep', 'OpenTime'], how = 'left')
    df_work['precision'] = abs((df_work['ClosePrice_y'] - df_work['ClosePrice_x']) / df_work['ClosePrice_y']) * 100

    result = round(df_work['precision'].mean(),2)
    print('erreur moyenne calculee : ' + str(result) + '%')



my_task = PythonOperator(
    task_id='check_precision_task',
    python_callable=get_result,
    dag=my_dag
)
