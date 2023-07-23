#%%
import sys
import os
sys.path.insert(0, os.path.abspath("../"))
sys.path.insert(0, os.path.abspath("../binance_bridge"))
from binance_bridge.schemas import Symbol, Kline as KlineSchema
from preprocessing import vwap

import numpy as np
import pandas as pd
import tensorflow as tf
import joblib

# input[input.Symbol == 'ADAUSDT']
class Model():
    _input_features_ = ['Symbol', 'Open Time', 'Open Price', 'High Price', 'Low Price', 'Close Price', 'Volume']

    def __init__(self, model, scaler):
        self._model = model
        self._scaler = scaler

    def forecast(self, input):
        """
        Input must contains 4 timesteps (4 rows) for each symbol.
        ! timesteps must be the same accross symbols.
        Input schema:
        [
            [<Symbol>, <Open Time>, <Open Price>, <High Price>, <Low Price>, <Close Price>]
        ]
        """
        # TODO: Check input
        # - timesteps range
        # - features len / type ?

        df_tmp = pd.DataFrame(input, columns=self._input_features_)
        types = {k:v for k, v in KlineSchema.items() if k in self._input_features_}
        datas = pd.DataFrame()
        for symbol in Symbol:
            asset = df_tmp[df_tmp.Symbol == symbol.value].drop(columns=['Symbol'])
            asset = asset.astype(types).set_index('Open Time').sort_index()
            datas[f'VWAP {symbol.value}'] = vwap(asset)
            datas[f'Upper {symbol.value}'] = asset['High Price'] - np.maximum(asset['Close Price'], asset['Open Price'])
            datas[f'Lower {symbol.value}'] = np.minimum(asset['Close Price'], asset['Open Price']) - asset['Low Price']

        X = self._scaler.transform(datas)
        preds = self._model.predict(X.reshape(1, 4, 15))
        return dict(zip(Symbol._member_map_.keys(), preds[0]))
