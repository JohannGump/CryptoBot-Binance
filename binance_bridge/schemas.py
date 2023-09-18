from enum import Enum

# Crypto currencies base/quote pairs
class Symbol(str, Enum):
    ADAUSDT = "ADAUSDT"
    BTCUSDT = "BTCUSDT"
    BNBUSDT = "BNBUSDT"
    ETHUSDT = "ETHUSDT"
    XRPUSDT = "XRPUSDT"

# Crypto currencies base/name pairs
class SymbolName(str, Enum):
    ADAUSDT = "Cardano"
    BTCUSDT = "Bitcoin"
    BNBUSDT = "BNB"
    ETHUSDT = "Ethereum"
    XRPUSDT = "Ripple"

# Kline Binance data <> Dataframe mapping
# ! Mapped in raw data order: need python >= 3.6
# https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-data
Kline = {
    'Open Time': 'datetime64[ns]',    # Kline open time
    'Open Price': 'float64',          # Open price
    'High Price': 'float64',          # High price
    'Low Price': 'float64',           # Low price
    'Close Price': 'float64',         # Close price
    'Volume': 'float64',              # Volume
    'Close Time': 'datetime64[ns]',   # Kline Close time
    'Quote Asset Volume': 'float64',  # Quote asset volume
    'Number Of Trades': 'int64',      # Number of trades
    'Taker Buy Base': 'float64',      # Taker buy base asset volume
    'Taker Buy Quote': 'float64',     # Taker buy quote asset volume
    'Unused': 'object'                # Unused field, ignore
}

# Samples interval
class TimeStep(str, Enum):
    MINUTELY = '1m'
    HOURLY = '1h'
    DAILY = '1d'
    WEEKLY = '1w'