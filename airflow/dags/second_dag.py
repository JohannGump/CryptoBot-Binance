import os
from airflow.decorators import dag, task
from datetime import datetime, timedelta

@dag(start_date=datetime(2023, 9, 19),
    schedule_interval='@once', 
    catchup=False)
def simple_test_dag():
    """
    ### Airflow integration testing
    """

    @task
    def task_1():
        """
        #### Task 1
        """
        print("task 1")

    @task
    def task_2():
        """
        #### Task 2
        """
        print("task 2")

    @task
    def task_3():
        """
        #### Task 3
        """
        print("task 3")

    t1 = task_1()
    t2 = task_2()
    t3 = task_3()
    t1 >> t2 >> t3

simple_test_dag()
