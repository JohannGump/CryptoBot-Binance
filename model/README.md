# CryptoBot Model

Our model architecture is based on a Recurrent Neural Network (LSTM).

## Input & ouput format at inference time

On deployed models, input data does not need to be preprocessed, entry layers handle features extraction and preprocessing.

Models outputs price returns at [+N timestep] for all registered symbols in one pass.

Input "raw features" values is comprised of:
- Open Price
- High Price
- Low Price
- Close Price
- Volume

This "raw features" values must be present for all sequences/symbols with respect to the following order.

```python
[<Open Price>, <High Price>, <Low Price>, <Close Price>, <Volume>]
```

A sequence is composed of N consecutive timesteps and one sequence must be given per crypto-pair (ie. [Symbol](../binance_bridge/schemas.py)). All sequences of a batch must start at the same timestep and contain the same number of timesteps.

```python
# Sequence of "raw features" for a symbol
[
    [<Open Price>, <High Price>, <Low Price>, <Close Price>, <Volume>] # ts
    [<Open Price>, <High Price>, <Low Price>, <Close Price>, <Volume>] # ts + 1
    [<Open Price>, <High Price>, <Low Price>, <Close Price>, <Volume>] # ts + 2
    [<Open Price>, <High Price>, <Low Price>, <Close Price>, <Volume>] # ts + 3
]
```

### Example

Following the current symbols list: _ADAUSDT_, _BTCUSDT_, _BNBUSDT_, _ETHUSDT_, _XRPUSDT_.  
The given input, sequences of 4 timesteps (4 consecutive hours for each symbol):

```python
# Input shape (, len(<symbols>), len(<raw features>))
# Note that the sequences must be sorted by symbols order and "raw features"
# values by time ascending order.
[
  [                                              # ADAUSDT
    [0.3144, 0.316, 0.3142, 0.316, 1074768.0],   # 2023-07-23 07:00:00
    [0.3159, 0.317, 0.3152, 0.3162, 2261017.8],  # 2023-07-23 08:00:00
    [0.3163, 0.3165, 0.315, 0.3151, 1629951.6],  # 2023-07-23 09:00:00
    [0.3151, 0.3152, 0.315, 0.3151, 63508.5]     # 2023-07-23 10:00:00
  ],
  [                                              # BTCUSDT
    [29919.4, 29930.2, 29885.0, 29916.0, 467.9], # 2023-07-23 07:00:00
    [29916.0, 29959.0, 29887.6, 29948.0, 712.2], # 2023-07-23 08:00:00
    [29948.0, 29955.6, 29896.8, 29900.1, 431.8], # 2023-07-23 09:00:00
    [29900.1, 29905.3, 29897.7, 29901.8, 68.8]   # 2023-07-23 10:00:00
  ],
  [                                              # BNBUSDT
    [242.6, 242.8, 242.2, 242.6, 5893.995],      # 2023-07-23 07:00:00
    [242.6, 243.0, 242.3, 243.0, 6496.529],      # 2023-07-23 08:00:00
    [243.0, 243.0, 242.0, 242.2, 4951.126],      # 2023-07-23 09:00:00
    [242.1, 242.3, 242.1, 242.3, 653.924]        # 2023-07-23 10:00:00
  ],
  [                                              # ETHUSDT
    [1874.2, 1875.0, 1872.54, 1875.04, 2549.9],  # 2023-07-23 07:00:00
    [1875.0, 1878.3, 1873.8, 1878.06, 3372.1],   # 2023-07-23 08:00:00
    [1878.0, 1878.4, 1874.65, 1874.99, 2526.8],  # 2023-07-23 09:00:00
    [1874.9, 1875.8, 1874.99, 1875.53, 527.1]    # 2023-07-23 10:00:00
  ],
  [                                              # XRPUSDT
    [0.7419, 0.7427, 0.7364, 0.73, 9995797.0],   # 2023-07-23 07:00:00
    [0.7382, 0.7478, 0.7356, 0.74, 18607219.0],  # 2023-07-23 08:00:00
    [0.7424, 0.7443, 0.7366, 0.73, 11006535.0],  # 2023-07-23 09:00:00
    [0.7384, 0.7394, 0.7379, 0.73, 1596575.0]    # 2023-07-23 10:00:00
  ]
]
```

Would give us:

```python
# Predicted Prices Return at +4 hours (2023-07-23 14:00:00)
# Note that the output is ordered as the input sequences order (symbols order)
[
  [
    0.0524992868,  # ADAUSDT's PR
    -0.0411104187, # BTCUSDT's PR
    0.0772442296,  # BNBUSDT's PR
    0.0939322114,  # ETHUSDT's PR
    0.0153770773   # XRPUSDT's PR
  ]
]
```