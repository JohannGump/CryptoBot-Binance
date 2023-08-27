"""Model training and building.

Core keras RNN wrapped into final model with integrated input (pre)processing.
Models are saved into ../model_fit/<timestep>.

Usage
-----
Beware that data must be availaible for the given timestep (default to hourly)
in MySQL dedicated DB.

Build an hourly timestep model (execute cmd from the script's folder)
>>> python train.py

Build a model for another timestep, define the MODEL_TIMESTEP env variable
to the desired timestep
>>> MODEL_TIMESTEP=weekly python train.py

Should give us to saved models
    ../model_fit/hourly
    ../model_fit/weekly
"""
import sys
import os

sys.path.insert(0, os.path.abspath("../"))
sys.path.insert(0, os.path.abspath("../binance_bridge"))
from binance_bridge.schemas import Symbol, TimeStep
import preprocessing as pp

import mysql.connector
import pandas as pd
import tensorflow as tf

# Core model training
# -------------------

TIMESTEP = os.getenv('MODEL_TIMESTEP', TimeStep.HOURLY.name).upper()
INPUT_SEQUENCE_LENGTH = 4
OUTPUT_TIMESTEP = 4
TEST_SAMPLES_N = INPUT_SEQUENCE_LENGTH * 3

cnx = mysql.connector.connect(
    host=os.getenv('KLINESDB_HOST', 'localhost'),
    user=os.getenv('KLINESDB_USER', 'root'),
    password=os.getenv('KLINESDB_PASSWORD', 'root'),
    database=os.getenv('KLINESDB_DBNAME', 'klines'),
    port=os.getenv('KLINESDB_PORT', '3306'))

feats = None
targs = None

# table column / feature name mapping
ftmap = dict(zip([s.replace(' ', '') for s in pp.RAW_FEATURES], pp.RAW_FEATURES))

for symbol in sorted(Symbol):
    query = "SELECT * FROM hist_klines WHERE TimeStep = %s AND Symbol = %s"
    asset = pd.read_sql(query, cnx, params=[TIMESTEP, symbol.name], index_col='OpenTime') \
        .rename(ftmap, axis=1) \
        .sort_index() \
        [:-TEST_SAMPLES_N] \
        [pp.RAW_FEATURES]
    if feats is None:
        feats = pd.DataFrame(index=asset.index)
        targs = pd.DataFrame(index=asset.index)
    feats = feats.join(pp.compute_features(asset), rsuffix=f' {symbol.value}')
    targs = targs.join(pp.compute_targets(asset, OUTPUT_TIMESTEP), rsuffix=f' {symbol.value}')

feats = feats[:-INPUT_SEQUENCE_LENGTH]
targs = targs[:-INPUT_SEQUENCE_LENGTH]

normalizer = tf.keras.layers.Normalization()
rounded = (len(feats)  // INPUT_SEQUENCE_LENGTH) * INPUT_SEQUENCE_LENGTH
normalizer.adapt(feats[:rounded].to_numpy().reshape(-1, INPUT_SEQUENCE_LENGTH, feats.shape[1]))

Ds = tf.keras.utils.timeseries_dataset_from_array(
    data=feats, targets=targs, sequence_stride=1,
    sequence_length=INPUT_SEQUENCE_LENGTH, batch_size=32)

model = tf.keras.models.Sequential()
model.add(normalizer)
model.add(tf.keras.layers.LSTM(128, return_sequences=False))
model.add(tf.keras.layers.Dense(len(targs.columns)))

model.compile(tf.keras.optimizers.Adam(), loss='mse', metrics=['mae'])
history = model.fit(Ds, epochs=1)

# TODO: writes log fit history

# Final model build
# -----------------
# Saved in SavedModel's format to support processing layers
# (https://github.com/keras-team/keras/issues/15348#issuecomment-974747528)

saved_model = tf.keras.models.Sequential()
saved_model.add(tf.keras.Input(shape=(INPUT_SEQUENCE_LENGTH, len(Symbol))))
saved_model.add(pp.RawSeqToFeatures(sequence_length=INPUT_SEQUENCE_LENGTH))
saved_model.add(model)

# TODO: handle model version
saved_model.save(f'../model_fit/{TIMESTEP.lower()}/1')