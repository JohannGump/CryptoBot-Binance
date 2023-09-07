import pytest
from main import get_binance_last_klines
import datetime
import os
from schemas import Symbol, TimeStep
import logging
from datetime import datetime, timedelta

#print dependencies versions used
print("pytest version:", pytest.__version__)

# Test cases
@pytest.mark.parametrize("symbol, interval", [
    (Symbol.ADAUSDT, "1h"),  # Test for Symbol ADAUSDT with interval 1h
    (Symbol.BTCUSDT, "1m"), # Test for Symbol BTCUSDT with interval 30m
    ("INVALID SYMBOL", "4h"),  # Test for Symbol ETHUSDT with interval 4h
])


def compute_start_time(interval: TimeStep, delta: int = 4):
    param = dict(zip(TimeStep, ['minutes', 'hours', 'days', 'weeks']))[interval]
    param = {param: delta}
    return datetime.now() - timedelta(**param)

# Test cases
def test_get_binance_last_klines_default_start_time(symbol: Symbol, ts: TimeStep, start_time: int):
    
    ts = os.getenv('TIMESTEP', TimeStep.HOURLY.name).upper()
    if ts not in TimeStep.__members__.keys():
        logging.error(f"'{ts}' is not a valid timestep, please use one of {[t.name for t in TimeStep]}")
        exit(1)

    ts = TimeStep[ts]
    start_time = compute_start_time(ts)

    data = get_binance_last_klines(symbol, ts, int(start_time.timestamp()*1000))

    if symbol == "INVALID SYMBOL":
        assert data is None
    else:
    # the API is reponding right

        # Check if the data is not None
        assert data is not None

        # Check if data is instance of list
        assert isinstance(data, list)

        # Check that we collect the good number of data points
        if ts == "1h":
            assert len(data) == 4
        elif ts == "1m":
            assert len(data) == 240

        # Check if each entry in data is a tuple with 7 elements (symbol, open_time, open_price, high_price, low_price, close_price, volume)
        for entry in data:
            assert isinstance(entry, tuple)
            assert len(entry) == 7
            assert all(isinstance(item, (str, float, int, Symbol, datetime.datetime)) for item in entry)

