"""Model training and building.

Core keras RNN wrapped into final model with integrated input (pre)processing.
Models are saved into /model_fit/<timestep unit>/<version>, ex:
    /model_fit/hourly/1
"""

import sys
import os

sys.path.insert(0, os.path.abspath("../"))
sys.path.insert(0, os.path.abspath("../binance_bridge"))
from binance_bridge.schemas import Symbol
import preprocessing as pp

import pandas as pd
import tensorflow as tf

# Core model training
# -------------------

INPUT_SEQUENCE_LENGTH = 4
OUTPUT_TIMESTEP = 4
TEST_SAMPLES_N = INPUT_SEQUENCE_LENGTH * 3

feats = None
targs = None
for symbol in Symbol:
    asset = pd.read_csv(f'../training_data/{symbol.value}.csv')[:-TEST_SAMPLES_N] \
        .set_index('Open Time').sort_index()[pp.RAW_FEATURES]
    if feats is None:
        feats = pd.DataFrame(index=asset.index)
        targs = pd.DataFrame(index=asset.index)
    feats = feats.join(pp.compute_features(asset), lsuffix=symbol.value)
    targs = targs.join(pp.compute_targets(asset, OUTPUT_TIMESTEP), lsuffix=symbol.value)

feats = feats[:-INPUT_SEQUENCE_LENGTH]
targs = targs[:-INPUT_SEQUENCE_LENGTH]

normalizer = tf.keras.layers.Normalization()
normalizer.adapt(feats.to_numpy().reshape(-1, INPUT_SEQUENCE_LENGTH, feats.shape[1]))

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

# TODO: handle parametrizable timestep unit and version
saved_model.save('../model_fit/hourly/1')