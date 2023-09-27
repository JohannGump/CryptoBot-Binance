from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
import datetime

my_dag = DAG(
    dag_id='hello_world',
    description='print hello',
    tags=['CryptoBot'],
    schedule_interval=None,
    default_args={
        'owner': 'airflow',
        'start_date': days_ago(2),
    }
)





# definition of the function to execute
def print_hello():
    print('Hello from Airflow')





my_task = PythonOperator(
    task_id='print_hello_task',
    python_callable=print_hello,
    dag=my_dag
)
