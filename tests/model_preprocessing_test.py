import os
import sys
import numpy as np
import pytest
import tensorflow as tf
sys.path.insert(0, os.path.abspath("./"))
sys.path.insert(0, os.path.abspath("./model"))
sys.path.insert(0, os.path.abspath("./binance_bridge"))
from binance_bridge.schemas import Symbol
import model.preprocessing as preproc
from model.preprocessing import vwap

def test_input_layer_shape():
    """Test model input shape.

    Input shape dims should be (see model/README.md):
        (<len(Symbol)>, <MODEL_INPUTSEQ_LENGTH>, <RAW_FEATURES>)
    """
    d1 = len(Symbol)
    d2 = preproc.MODEL_INPUTSEQ_LENGTH
    d3 = len(preproc.RAW_FEATURES)
    # We don't care about the values
    seqs = np.random.rand(d1, d2, d3)
    layer = preproc.RawSeqToFeatures(d1, d2, d3)
    try:
        layer(seqs)
    except Exception as e:
        assert False, f"Input shape should be ({d1}, {d2}, {d3})"

@pytest.fixture
def example_data():
    data = np.array([[1.0, 2.0, 3.0, 4.0, 5.0], [2.0, 3.0, 4.0, 5.0, 6.0]], dtype=np.float32)
    return tf.constant(data)

def test_vwap(example_data):
    result = vwap(example_data)
    expected_result = np.array([1.6666666, 2.2857144], dtype=np.float32)

    np.testing.assert_allclose(result, expected_result, rtol=1e-6)