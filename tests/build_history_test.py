import sys
import os
sys.path.insert(0, os.path.abspath("./"))
sys.path.insert(0, os.path.abspath("./data"))
sys.path.insert(0, os.path.abspath("./binance_bridge"))
from binance_bridge.schemas import Symbol, TimeStep
from binance_bridge.klines import binance_raw_klines, raw_klines_to_pandas
from data.build_history import connect, any_function

def test_connect():    
    assert True

def test_any_function():
    assert any_function() == 1



    