"""Preprocessing utilities.

For the most, we try to reuse the same functions for the training phase and the
final model. That mean preprocessing is mostly done with Tensorflow ops.

Features extraction / processing are based on the flollowing input schema,
beware that "column" ordering must be respected and rows should be in time 
ascending order (in respect with the underlying model)

    [<Open Price>, <High Price>, <Low Price>, <Close Price>, <Volume>]
"""

import os
import pandas as pd
import tensorflow as tf

MODEL_INPUTSEQ_LENGTH = int(os.getenv('MODEL_INPUTSEQ_LENGTH', 4))
MODEL_OUTPUT_SPAN = int(os.getenv('MODEL_OUTPUT_SPAN', 4))
RAW_FEATURES = ['Open Price', 'High Price', 'Low Price', 'Close Price', 'Volume']

@tf.function(input_signature=[tf.TensorSpec(shape=None, dtype=tf.float32)])
def vwap(x):
    """Returns the Weighted Average Price.

    VWAP = [Cumulative (Price * Volume)] / [Cumulative Volume]
    Where Price is the typical price in our case.
    """
    typical_price = (x[..., 1] + x[..., 2] + x[..., 3]) / tf.constant(3.)
    volume_typical_price = typical_price * x[..., 4]
    cumulative_volume_typical_price = tf.cumsum(volume_typical_price, axis=-1)
    cumulative_volume =  tf.cumsum(x[..., 4], axis=-1)
    return cumulative_volume_typical_price / cumulative_volume

@tf.function(input_signature=[tf.TensorSpec(shape=None, dtype=tf.float32)])
def upper_shadow(x):
    """Returns the upper price shadow."""
    prmax = tf.math.maximum(x[..., 3], x[..., 0])
    ushad = x[..., 1] - prmax
    return ushad

@tf.function(input_signature=[tf.TensorSpec(shape=None, dtype=tf.float32)])
def lower_shadow(x):
    """Returns the lower price shadow."""
    prmin = tf.math.minimum(x[..., 3], x[..., 0])
    lshad = prmin - x[..., 2]
    return lshad

def compute_features(asset: pd.DataFrame):
    """Returns the computed features for training.
    
    Input must comprise data for one symbol only and index should be sorted
    in time ascending order."""
    feats = pd.DataFrame(index=asset.index)
    feats['VWAP'] = vwap(asset)
    feats['Upper Shadow'] = upper_shadow(asset)
    feats['Lower Shadow'] = lower_shadow(asset)
    return feats

def compute_targets(asset: pd.DataFrame, timestep: int):
    """Returns target values for training.

    Where the target is log returns of the close price (rate of change).
    Input must comprise data for one symbol only and index should be sorted
    in time ascending order.
    """
    targs = pd.DataFrame(index=asset.index)
    targs[f'At +{timestep}'] = asset['Close Price'] \
        .pct_change(periods=timestep) \
        .shift(-timestep)
    return targs

# Prevent registration exception during development
tf.keras.saving.get_custom_objects().pop('cryptobot>RawSeqToFeatures', None)

@tf.keras.saving.register_keras_serializable(package='cryptobot')
class RawSeqToFeatures(tf.keras.layers.Layer):
    """Preprocessing features layer.

    Transform raw input to input features used by the model.
    See README for the used raw input format.
    """
    def __init__(self, symbol_count: int, sequence_length: int, raw_feature_count: int):
        super(RawSeqToFeatures, self).__init__()
        self._symbol_count = symbol_count
        self._sequence_length = sequence_length
        self._raw_feature_count = raw_feature_count

    def call(self, x):
        tf.debugging.assert_shapes(
            [(x, (self._symbol_count, self._sequence_length, self._raw_feature_count))],
            message="Wrong input shape")
        return self._compute_features(x)

    def _compute_features(self, x):
        pvwap = vwap(x)
        ushad = upper_shadow(x)
        lshad = lower_shadow(x)
        feats = tf.stack([pvwap, ushad, lshad], -1)
        feats = tf.transpose(feats, perm=(1, 0, 2))
        return tf.reshape(feats, (feats.shape[0], -1))

    def get_config(self):
        return {
            'symbol_count': self._symbol_count,
            'sequence_length': self._sequence_length,
            'raw_feature_count': self._raw_feature_count
        }