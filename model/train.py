#%%
import sys
import os
sys.path.insert(0, os.path.abspath("../"))
sys.path.insert(0, os.path.abspath("../binance_bridge"))
from binance_bridge.schemas import Symbol
from preprocessing import vwap
from model import Model

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
import joblib

#%% Load historical data
test_s = 4
window = 4
seqs_s = 4

datas= {}
for symbol in Symbol:
    datas[symbol] = pd.read_csv(f'../training_data/{symbol.value}.csv')[:-test_s]

cryptos = {}
columns = ['Open Price', 'High Price', 'Low Price', 'Close Price', 'Volume']
for symbol in Symbol:
    asset = datas.get(symbol).set_index('Open Time')[columns]
    asset['VWAP'] = vwap(asset)
    asset['Upper Shadow'] = asset['High Price'] - np.maximum(asset['Close Price'], asset['Open Price'])
    asset['Lower Shadow'] = np.minimum(asset['Close Price'], asset['Open Price']) - asset['Low Price']
    asset[f'Returns +{window}'] = asset['Close Price'].pct_change(periods=window).shift(-window)
    cryptos[symbol] = asset[:-window]

index = cryptos[Symbol.ADAUSDT].index
feats = pd.DataFrame(index=index)
targs = pd.DataFrame(index=index)
for symbol, asset in cryptos.items():
    feats[f'VWAP {symbol.value}'] = asset['VWAP']
    feats[f'Upper {symbol.value}'] = asset['Upper Shadow']
    feats[f'Lower {symbol.value}'] = asset['Lower Shadow']
    targs[f'Returns +{window} {symbol.value}'] = asset[f'Returns +{window}']

df_Xs = feats
df_ys = targs

scaler = StandardScaler()
Xs = scaler.fit_transform(df_Xs)

Xs = tf.keras.utils.timeseries_dataset_from_array(data=Xs, targets=df_ys, sequence_stride=1, sequence_length=seqs_s, batch_size=32)

model = tf.keras.models.Sequential()
model.add(tf.keras.layers.LSTM(128, return_sequences=False))
model.add(tf.keras.layers.Dense(len(targs.columns)))

model.compile(tf.keras.optimizers.Adam(), loss='mse', metrics=['mae'])
history = model.fit(Xs, epochs=1)

# TODO: writes log fit history

#%% Save model and scaler
model_api = Model(model, scaler)
joblib.dump(model_api, '../model_fit/model_v.joblib')