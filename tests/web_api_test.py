import os
import sys
import pytest
from fastapi.testclient import TestClient
sys.path.insert(0, os.path.abspath("./"))
from unittest import mock
from pytest import MonkeyPatch
monkeypatch = MonkeyPatch()
monkeypatch.chdir('web_api')
from web_api.main import app
from binance_bridge.schemas import SymbolName, TimeStep

@pytest.fixture
def client():
    return TestClient(app)

@mock.patch('mysql.connector.connect')
def test_index_route(mock_connect, client):
    """Test landing page.
    This should display all symbols fullnames and links to forecasts pages.
    Uggly, we assume a specific query against the database.
    """
    mock_cursor = mock_connect.return_value.cursor.return_value
    mock_cursor.fetchall.return_value = [{"NowClosePrice":0.2678,"Symbol":"ADAUSDT","TimeStep":"DAILY","InTime":"2023-10-02T10:37:09","OpenTime":"2023-10-06T02:00:00","PctChange":0.131289542,"ClosePrice":0.3029593393476},{"NowClosePrice":221.4,"Symbol":"BNBUSDT","TimeStep":"DAILY","InTime":"2023-10-02T10:37:09","OpenTime":"2023-10-06T02:00:00","PctChange":-0.0834688097,"ClosePrice":202.92000553242},{"NowClosePrice":28458.01,"Symbol":"BTCUSDT","TimeStep":"DAILY","InTime":"2023-10-02T10:37:09","OpenTime":"2023-10-06T02:00:00","PctChange":0.147964522,"ClosePrice":32668.78584672122},{"NowClosePrice":1741.42,"Symbol":"ETHUSDT","TimeStep":"DAILY","InTime":"2023-10-02T10:37:09","OpenTime":"2023-10-06T02:00:00","PctChange":0.131901667,"ClosePrice":1971.11620094714},{"NowClosePrice":0.5245,"Symbol":"XRPUSDT","TimeStep":"DAILY","InTime":"2023-10-02T10:37:09","OpenTime":"2023-10-06T02:00:00","PctChange":0.018694846,"ClosePrice":0.534305446727}]
    response = client.get('/')
    assert response.status_code == 200
    for s in SymbolName:
        assert bytes(s.value, 'utf-8') in response.content
        assert bytes(f'/forecast/{s.name.lower()}/daily', 'utf-8') in response.content

@mock.patch('mysql.connector.connect')
def test_forecast_route(_, client):
    """Test forecast endpoints
    A page must exists for all symbols and timesteps.
    Those should return HTTP 200 status code but without content (just a message
    for the user) since we don't fake data.
    """
    for s in SymbolName:
        for t in TimeStep:
            response = client.get(f'/forecast/{s.name.lower()}/{t.name.lower()}')
            assert response.status_code == 200

def test_routes_no_db(client):
    """Test endpoints without DB connnection.
    Those should return HTTP 204 status code with a message displayed to the user.
    """
    response = client.get('/')
    assert response.status_code == 204
    for s in SymbolName:
        for t in TimeStep:
            response = client.get(f'/forecast/{s.name.lower()}/{t.name.lower()}')
            assert response.status_code == 204