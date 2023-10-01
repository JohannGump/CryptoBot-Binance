import os
import sys
import pytest
sys.path.insert(0, os.path.abspath("../"))
sys.path.insert(0, os.path.abspath("../web_api"))
from unittest.mock import MagicMock, patch
from web_api.main import connect, app
from fastapi.testclient import TestClient

def test_connect():
    with patch('mysql.connector.connect') as mock_connect:
        # Configure the mock to return a connection
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection

        # Call the function
        connection = connect()

        # Assertions
        assert connection == mock_connection
        mock_connect.assert_called_once_with(
            host=os.getenv('MYSQL_HOST_PREDICTIONS'),
            user=os.getenv('MYSQL_USER_PREDICTIONS'),
            password=os.getenv('MYSQL_PASSWORD_PREDICTIONS'),
            database=os.getenv('MYSQL_DATABASE_PREDICTIONS')
        )

@pytest.fixture
def client():
    return TestClient(app)

def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Welcome to Cryptobot app' in response.data

def test_forecast_route(client):
    symbol = 'btcusdt'
    timestep = 'minute'
    response = client.get(f'/forecast/{symbol}/{timestep}')
    assert response.status_code == 200
    assert b'Forecast for' in response.data