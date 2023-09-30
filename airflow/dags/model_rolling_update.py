import os
from airflow.decorators import dag, task
from datetime import datetime, timedelta
import requests

@dag(start_date=datetime(2023, 9, 30),
    schedule_interval=timedelta(hours=24),
    catchup=False)
def models_rolling_update():
    """
    ### Trigger Github models fit & deployment workflow
    """
    @task
    def trigger_ghci():
        """
        #### Request the Github workflow
        """
        url = "https://api.github.com/repos/JohannGump/CryptoBot-Binance/dispatches"
        gh_token = os.getenv('GITHUB_DISPATCH_TOKEN', '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')
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"token {gh_token}"
        }
        payload = {
            "event_type": "model-rolling-update",
            "client_payload": {
                "max_samples_fit": 20000
            }
        }
        res = requests.post(url, headers=headers, json=payload)
        if res.status_code > 300:
            raise Exception(res.json())

    trigger_ghci()

models_rolling_update()