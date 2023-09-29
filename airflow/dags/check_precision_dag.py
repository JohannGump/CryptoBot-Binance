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
    schedule_interval="* * * * *",
    default_args={
        'owner': 'airflow',
        'start_date': days_ago(2),
    },
    catchup=False
)


klin_conn = {
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

def generate_df_work():
    df_klines = sql_to_df(klin_conn, 'klines')
    df_predictions = sql_to_df(klin_conn, 'predictions')
    df_work = df_predictions.merge(right = df_klines, on = ['Symbol', 'TimeStep', 'OpenTime'], how = 'left')
    df_work['precision'] = abs((df_work['ClosePrice_y'] - df_work['ClosePrice_x']) / df_work['ClosePrice_y']) * 100
    return df_work

def create_global_table(connector):
    connexion = mysql.connector.connect(**connector)
    curseur = connexion.cursor()
    query = """
    CREATE TABLE IF NOT EXISTS hist_global_precision (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATETIME,
    precision_rate DOUBLE
    )
    """
    curseur.execute(query)
    curseur.close()
    connexion.close()
    print('table hist_global_precision created')

def create_detailed_table(connector):
    connexion = mysql.connector.connect(**connector)
    curseur = connexion.cursor()
    query = """
    CREATE TABLE IF NOT EXISTS hist_detailed_precision (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATETIME,
    symbol VARCHAR(255),
    timestep VARCHAR(255),
    precision_rate DOUBLE
    )
    """
    curseur.execute(query)
    curseur.close()
    connexion.close()
    print('table hist_detailed_precision created')

def insert_data(req, data, connector):
    connexion = mysql.connector.connect(**connector)
    curseur = connexion.cursor()    
    curseur.execute(req, data)
    connexion.commit()
    curseur.close()
    connexion.close()



def get_global_precision():
    df_work = generate_df_work()
    result = round(df_work['precision'].mean(),2)
    create_global_table(klin_conn)
    print('erreur moyenne calculee : ' + str(result) + '%')
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    req = """
    INSERT INTO hist_global_precision (date, precision_rate)
    VALUES (%s, %s)
    """
    data = (date, result)
    insert_data(req, data, klin_conn)


def get_detailed_precision():
    df_work = generate_df_work()
    result = df_work[['Symbol', 'TimeStep', 'precision']].groupby(by=['Symbol', 'TimeStep']).mean()
    result = result.reset_index()
    create_detailed_table(klin_conn)
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for index, row in result.iterrows():
        print(row['Symbol'], row['TimeStep'], round(row['precision'],2))
        req = """
        INSERT INTO hist_detailed_precision (date, symbol, timestep, precision_rate)
        VALUES (%s, %s, %s, %s)
        """
        data = (date, row["Symbol"], row["TimeStep"], round(row["precision"], 2))
        insert_data(req, data, klin_conn)




my_task1 = PythonOperator(
    task_id='check_global_precision_task',
    python_callable=get_global_precision,
    dag=my_dag
)

my_task2 = PythonOperator(
    task_id='check_detailed_precision_task',
    python_callable=get_detailed_precision,
    dag=my_dag
)


