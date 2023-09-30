import os
from airflow.decorators import dag, task
from datetime import datetime, timedelta
import mysql.connector
import requests

@dag(start_date=datetime(2023, 9, 19),
    schedule_interval='@once', 
    catchup=False)
def test_services_dag():
    """
    ### Airflow integration testing
    """
    @task
    def test_db():
        """
        #### DB connection testing
        """
        conn = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST_PREDICTIONS'),
            user=os.getenv('MYSQL_USER_PREDICTIONS'),
            password=os.getenv('MYSQL_PASSWORD_PREDICTIONS'),
            database=os.getenv('MYSQL_DATABASE_PREDICTIONS',) 
        )
        curs = conn.cursor()
        curs.execute("SELECT * FROM predictions LIMIT 1")
        print(curs.fetchall())
        curs.close()
        conn.close()

    @task
    def test_model_api():
        """
        #### TFX model api connection testing
        """
        host = os.getenv('PREDICT_SERVER_HOST')
        res = requests.get(f"http://{host}/v1/models/hourly")
        print(res.content)

    @task
    def test_web_api():
        """
        #### Web api connection testing
        """
        host = os.getenv('WEB_API_HOST')
        res = requests.get(f"http://{host}")
        print(res.content)

    t1 = test_db()
    t2 = test_model_api()
    t3 = test_web_api()
    t1 >> t2 >> t3

test_services_dag()
