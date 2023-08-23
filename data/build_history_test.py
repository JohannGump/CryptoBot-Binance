import sys
import os
sys.path.insert(0, os.path.abspath("./"))
sys.path.insert(0, os.path.abspath("./binance_bridge"))
from binance_bridge.schemas import Symbol, TimeStep
from binance_bridge.klines import binance_raw_klines, raw_klines_to_pandas
from build_history import connect

def test_connect():
    connection = connect()
    assert connection == 1

    