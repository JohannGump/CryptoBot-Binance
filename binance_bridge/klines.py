"""Set of utilities to fetch data from Binance API.

Only klines/candlesticks are considered at the time being. Fetched data are
converted to pandas Dataframe for ease of manipulation (excepted for `binance_raw_klines`).
See `Symbol` enum for the accepted Crypto currencies.

Examples
--------
Get the last 10000 hours of Etherum USDT klines:

>>> from schemas import Symbol
>>> eth_klines = get_historical_klines(Symbol.ETHUSDT, amount=10000)

Alternatively we can fetch from `historical klines`generator in order to
process data in between:

>>> for batch in historical_klines(Symbol.ETHUSDT, amount=10000):
>>>     # ...process data (batch is a pandas Dataframe)
""" 
#%%
import time
import requests
import pandas as pd
from tqdm import tqdm
from schemas import Symbol, Kline as KlineSchema, TimeStep

# TODO: Compute Binance exchange rate limit from their API
# endpoint: https://api.binance.com/api/v3/exchangeInfo
# ref: https://dev.binance.vision/t/what-are-the-ip-weights/280/2
# Last known exchange rate limit is 1200 reqs per minute
MBX_ALOW_WEIGHT1M = 1200
MBX_LAST_REQ_TIME = time.time()
MBX_LAST_WEIGHT1M = 0

def binance_raw_klines(symbol: Symbol, interval: TimeStep, start_time = None, end_time = None):
    """Requests Binance for 500 klines records.

    Note: Due to the Binance request rate limiter, this function may not return
    as fast as the API call.

    Parameters
    ----------
    symbol: Currency pair you want klines for
    inerval: TimeStep
        the samples time interval (ex. 1 sample per hour)
    start_time: int, optional
        period start, a timestamp in millis
    end_time: int, optional
        period end, a timestamp in in millis

    Returns
    -------
    list of klines data, see schema here:
    https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-data
    """
    global MBX_ALOW_WEIGHT1M, MBX_LAST_REQ_TIME, MBX_LAST_WEIGHT1M

    now = time.time()

    # Prevent heavy request rate
    # FEAT: refactor request rate handle to a function
    if MBX_LAST_WEIGHT1M >= MBX_ALOW_WEIGHT1M:
        time.sleep(now - MBX_LAST_REQ_TIME)
        return binance_raw_klines(symbol, start_time, end_time)

    if now - MBX_LAST_REQ_TIME > 60:
        MBX_LAST_REQ_TIME = now
        MBX_LAST_WEIGHT1M = 0

    endpoint = "https://data-api.binance.vision/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval
    }

    if start_time is not None:
        params["startTime"] = start_time

    if end_time is not None:
        params["endTime"] = end_time

    response = requests.get(endpoint, params=params)
    MBX_LAST_WEIGHT1M = int(response.headers["X-MBX-USED-WEIGHT-1M"])

    if response.status_code == 200:
        return response.json()

def raw_klines_to_pandas(raw_klines):
    """Convert raw klines data (Binance API res) to pandas Dataframe."""
    global KlineSchema

    data = pd.DataFrame(raw_klines, columns=KlineSchema.keys())
    data["Open Time"] = pd.to_datetime(data["Open Time"], unit="ms")
    data["Close Time"] = pd.to_datetime(data["Close Time"], unit="ms")
    data = data.astype(KlineSchema)
    data = data.drop(columns="Unused")
    return data

def historical_klines(symbol: Symbol, amount: int, interval: TimeStep):
    """Generates given amount of records by batches of 500.

    Batches are returned from recent to older one, starting from the date time now.
    Note: it is not guaranteed to get the total amount asked if the request exceeded
    Binance API historical data.

    Parameters
    ----------
    symbol: Currency pair you want klines for
    amount: Desired amount of records
    inerval: Samples time interval

    Returns
    -------
    Generator[pandas.Dataframe]
    """
    end_time = None
    while amount > 0:
        raw_data = binance_raw_klines(symbol, interval=interval, end_time=end_time)
        if raw_data is None or len(raw_data) == 0:
            break
        pds_data = raw_klines_to_pandas(raw_data)
        end_time = pds_data.iloc[0]["Open Time"] - pd.Timedelta(hours=1)
        end_time = int(end_time.timestamp() * 1000)
        amount-= len(pds_data)
        yield pds_data

def get_historical_klines(symbol = Symbol.BTCUSDT, amount = 500, interval: TimeStep = TimeStep.Hourly):
    """Returns given amount of kline records.

    Wraps `historical_klines` generator to concat batches in a single Dataframe.
    See `historical_klines` for parameters and constraints.
    Output a progress bar to indicate progression.
    """
    klines = None
    for data in tqdm(historical_klines(symbol, amount=amount, interval=interval), total=amount / 500):
        klines = data if klines is None else pd.concat([data, klines], ignore_index=True)
    return klines