import os
import sys
import numpy as np
sys.path.insert(0, os.path.abspath("./"))
sys.path.insert(0, os.path.abspath("./model"))
sys.path.insert(0, os.path.abspath("./binance_bridge"))
from binance_bridge.schemas import Symbol
import model.preprocessing as preproc

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