import pytest
from main import get_binance_last_klines
import datetime
from schemas import Symbol

#print dependencies versions used
print("pytest version:", pytest.__version__)

# Test cases
@pytest.mark.parametrize("symbol, interval", [
    (Symbol.ADAUSDT, "1h"),  # Test for Symbol ADAUSDT with interval 1h
    (Symbol.BTCUSDT, "1m"), # Test for Symbol BTCUSDT with interval 30m
    ("INVALID SYMBOL", "4h"),  # Test for Symbol ETHUSDT with interval 4h
])

# Test cases
def test_get_binance_last_klines_default_start_time(symbol, interval):
    
    data = get_binance_last_klines(symbol, interval)

    if symbol == "INVALID SYMBOL":
        assert data is None
    else:
    # the API is reponding right

        # Check if the data is not None
        assert data is not None

        # Check if data is instance of list
        assert isinstance(data, list)

        # Check that we collect the good number of data points
        if interval == "1h":
            assert len(data) == 4
        elif interval == "1m":
            assert len(data) == 240

        # Check if each entry in data is a tuple with 7 elements (symbol, open_time, open_price, high_price, low_price, close_price, volume)
        for entry in data:
            assert isinstance(entry, tuple)
            assert len(entry) == 7
            assert all(isinstance(item, (str, float, int, Symbol, datetime.datetime)) for item in entry)

