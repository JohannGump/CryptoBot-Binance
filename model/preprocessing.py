import numpy as np

def log_return(series, periods=1):
    return np.log(series).diff(periods=periods)

# Volume Weighted Average Price
def vwap(df):
    typical_price = (df['High Price'] + df['Low Price'] + df['Close Price']) / 3
    volume_typical_price = typical_price * df['Volume']
    cumulative_volume_typical_price = volume_typical_price.cumsum()
    cumulative_volume =  df['Volume'].cumsum()
    return cumulative_volume_typical_price / cumulative_volume

def add_features(asset):
    asset['VWAP'] = vwap(asset)
    asset['Upper Shadow'] = asset['High Price'] - np.maximum(asset['Close Price'], asset['Open Price'])
    asset['Lower Shadow'] = np.minimum(asset['Close Price'], asset['Open Price']) - asset['Low Price']
    return asset
