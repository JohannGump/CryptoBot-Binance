data_JSON_folder = '/src/add_crypto/'
filename_JSON = data_JSON_folder + '{pair}_binance_data.json'
volume_folder = '/src/training_data/'
filename_preprocessed = volume_folder + '{pair}.csv'
pip_time = "1h"

pairs = ['ADAUSDT', 
         'BTCUSDT', 
         'BNBUSDT', 
         'ETHUSDT', 
         'XRPUSDT']

label = {
    0 : 'Open Time',    # Kline open time
    1 : 'Open Price',          # Open price
    2 : 'High Price',          # High price
    3 : 'Low Price',           # Low price
    4 : 'Close Price',         # Close price
    5 : 'Volume',              # Volume
    6 : 'Close Time',   # Kline Close time
    7 : 'Quote Asset Volume',  # Quote asset volume
    8 : 'Number Of Trades',      # Number of trades
    9 : 'Taker Buy Base',      # Taker buy base asset volume
    10 : 'Taker Buy Quote',     # Taker buy quote asset volume
    11 : 'Unused'                # Unused field, ignore
}