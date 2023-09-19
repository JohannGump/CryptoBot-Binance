import os
from airflow.decorators import dag, task
from datetime import datetime, timedelta
import mysql.connector
import requests

@dag(start_date=datetime(2023, 9, 19), tags=['cryptobot'])
def test_dag():
    """
    ### Airflow integration testing
    """

    @task
    def test_db():
        """
        #### DB connection testing
        """
        conn = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST_KLINES'),
            user=os.getenv('MYSQL_USER_KLINES'),
            password=os.getenv('MYSQL_PASSWORD_KLINES'),
            database=os.getenv('MYSQL_DATABASE_KLINES',) 
        )
        curs = conn.cursor()
        curs.execute("SELECT * FROM klines LIMIT 1")
        print(curs.fetchall())
        curs.close()
        conn.close()

    @task
    def test_model_api():
        """
        #### TFX model api connection testing
        """
        api = os.getenv('PREDICT_API_URL')
        res = requests.get(f"{api}/v1/models/hourly")
        print(res.content)

    @task
    def test_web_api():
        """
        #### Web api connection testing
        """
        api = os.getenv('WEB_API_URL')
        res = requests.get(api)
        print(res.content)

    t1 = test_db()
    t2 = test_model_api()
    t3 = test_web_api()
    t1 >> t2 >> t3

test_dag()