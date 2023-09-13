"""One shot script that create schema and load / update historical data.

First execution may take some times to load full data, by default maximum samples
per symbol / timestep is limited to 100000, use KLINES_MAX_RECORDS_PER_SYTS env
variable to change it, ex:

>>> KLINES_MAX_RECORDS_PER_SYTS=45000 python build_history.py

.. Note:: Even if stored records are up to date, a small load is
triggered because of the differences between computed times and the ones
returned by Binance API.
"""

import os
import sys
import mysql.connector
import concurrent.futures
from datetime import datetime
import asyncio
from tqdm.asyncio import tqdm_asyncio
import pandas as pd
sys.path.insert(0, os.path.abspath("./"))
sys.path.insert(0, os.path.abspath("./binance_bridge"))
print(sys.path.insert(0, os.path.abspath("./binance_bridge")))
from binance_bridge.schemas import Symbol, TimeStep
from binance_bridge.klines import binance_raw_klines, raw_klines_to_pandas


# JLEB : test function to test with pytest
def any_function():
    return 1


# Maximum records allowed per symbol and timestamp
KLINES_MAX_RECORDS_PER_SYTS = int(os.getenv('KLINES_MAX_RECORDS_PER_SYTS', 100000))
TODAY = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

def connect():
    """Returns MySQL connection."""
    return mysql.connector.connect(
    host=os.getenv('KLINESDB_HOST', 'localhost'),
    user=os.getenv('KLINESDB_USER', 'root'),
    password=os.getenv('KLINESDB_PASSWORD', 'root'),
    database=os.getenv('KLINESDB_DBNAME', 'klines'),
    port=os.getenv('KLINESDB_PORT', '3306'))


# Historical data schema
# ----------------------

query = f"""
CREATE TABLE IF NOT EXISTS hist_klines (
    Symbol enum({','.join([f"'{s.name}'" for s in Symbol])}) NOT NULL,
    TimeStep enum({','.join([f"'{t.name}'" for t in TimeStep])}) NOT NULL,
    OpenTime DATETIME NOT NULL,
    OpenPrice DOUBLE NOT NULL,
    HighPrice DOUBLE NOT NULL,
    LowPrice DOUBLE NOT NULL,
    ClosePrice DOUBLE NOT NULL,
    Volume DOUBLE NOT NULL,
    UNIQUE INDEX idx_open_time (Symbol, TimeStep, OpenTime)
)
"""


# Utils / defs
# ----------------------

def timestep_delta_unit(ts: TimeStep):
    """Returns the unit of time used by pandas."""
    return dict(zip(TimeStep, ('T', 'H', 'D', 'W')))[ts]

def timestep_to_seconds(ts: TimeStep):
    """Returns the equivalent in seconds of a timestep."""
    return dict(zip(TimeStep, (60, 3600, 86400, 604800)))[ts]

def oldests_open_times():
    """Returns the list of oldests open times of each timestep / symbol.

    Since we make 'concurrent' calls to Binance API, function should be run
    asynchronously, ie. with `ThreadPoolExecutor` to ease result catching.

    Returns
    -------
    list of tuples in the form
        [(<TimeStep>, <Symbol>, <datetime>)]
    """
    async def oldest_record_date(timestep: TimeStep, symbol: Symbol):
        loop = asyncio.get_event_loop()
        dat = await loop.run_in_executor(
            None,
            lambda: binance_raw_klines(symbol, timestep, start_time=0, limit=1)
        )
        res = raw_klines_to_pandas(dat)
        return (timestep, symbol, res['Open Time'].loc[0])

    async def run():
        futures = []
        for ts in TimeStep:
            for symbol in Symbol:
                futures.append(oldest_record_date(ts, symbol))
        recs = await asyncio.gather(*futures)
        return recs

    return asyncio.run(run())

def etl_historical_klines(deltas):
    """Bulk loads and save klines of all symbols.

    Run each call to this function inside its proper thread in order
    to speed up the whole process.

    Parameters
    ----------
    deltas: list
        A list of tuples in the form
        (<TimeStep>, <Symbol>, <start_time:datetime>, <end_time:datetime>).
    """
    cnx = connect()
    dcols = ['Open Time', 'Open Price', 'High Price', 'Low Price', 'Close Price', 'Volume']
    query = """
    INSERT INTO hist_klines
        (Symbol, TimeStep, OpenTime, OpenPrice, HighPrice, LowPrice, ClosePrice, Volume)
        VALUES (%(Symbol)s, %(Timestep)s, %(Open Time)s, %(Open Price)s, %(High Price)s, %(Low Price)s, %(Close Price)s, %(Volume)s)
        ON DUPLICATE KEY UPDATE Symbol=Symbol, TimeStep=TimeStep, OpenTime=OpenTime
    """

    async def etl_klines(symbol:Symbol, interval:TimeStep, start_time:datetime, end_time:datetime):
        loop = asyncio.get_event_loop()
        raw_data = await loop.run_in_executor(
            None,
            lambda: binance_raw_klines(
                symbol,
                interval=interval,
                start_time=int(start_time.timestamp() * 1000),
                end_time=int(end_time.timestamp() * 1000))
        )
        if raw_data is None or len(raw_data) == 0:
            return
        data = raw_klines_to_pandas(raw_data)
        data = data[dcols]
        data = data.astype({'Open Time': str})
        data = data.assign(Symbol=symbol.name, Timestep=interval.name.lower())
        cursor = cnx.cursor(dictionary=True)
        cursor.executemany(query, data.to_dict(orient='records'))
        cursor.close()
        cnx.commit()

    async def run(deltas):
        tasks = []
        for interval, symbol, end_time, ctime in deltas:
            delta = pd.Timedelta(500, timestep_delta_unit(interval))
            while True:
                etime = ctime
                ctime = ctime - delta
                if ctime < end_time:
                    ctime = end_time
                tasks.append(etl_klines(symbol, interval, ctime, etime))
                if ctime == end_time:
                    break
        res = await tqdm_asyncio.gather(*tasks)
        return res

    asyncio.run(run(deltas))
    cnx.close()




if __name__ == "__main__":
    cnx = connect()
    cursor = cnx.cursor()
    cursor.execute(query)
    cursor.close()

    # Load / update historical data
    # -----------------------------
    # We build a table of deltas 'oldest open time' (StartTime) - 'today' (EndTime)
    # and intersects it with already stored data.

    # Deltas table
    print("Computes times deltas from Binance API...")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(oldests_open_times)
        open_times = future.result()

    deltas = pd.DataFrame(open_times, columns=['TimeStep', 'Symbol', 'OpenTime'])
    deltas = deltas.groupby('TimeStep')['OpenTime'].max()
    mxrecs = (TODAY - deltas) \
        .to_frame('delta') \
        .apply(lambda x: x.delta.total_seconds() // timestep_to_seconds(x.name), axis=1)
    mxrecs = mxrecs.where(
        mxrecs < KLINES_MAX_RECORDS_PER_SYTS,
        other=KLINES_MAX_RECORDS_PER_SYTS)
    deltas = deltas.to_frame().assign(
        StartTime=(
            mxrecs.to_frame('nrecs').apply(
                lambda x: TODAY - pd.Timedelta(x.nrecs, timestep_delta_unit(x.name)),
                axis=1)),
        EndTime=TODAY)
    deltas = deltas.rename(index={ts:ts.name for ts in TimeStep})

    # Stored data
    cnx = connect()
    query = """
    SELECT TimeStep, Symbol,
        MIN(OpenTime) 'StartTime', MAX(OpenTime) 'EndTime',
        COUNT(*) 'TotalRecs'
    FROM hist_klines
    GROUP BY TimeStep, Symbol
    """
    records = pd.read_sql_query(query, cnx, index_col=['TimeStep', 'Symbol'])
    cnx.close()

    records = pd.DataFrame(
        index=pd.MultiIndex.from_product(
            [[ts.name for ts in TimeStep], [sy.name for sy in Symbol]],
            names=['TimeStep', 'Symbol'])) \
        .join(records) \
        .astype({'StartTime': 'datetime64[ns]', 'EndTime': 'datetime64[ns]'})

    # Intersect deltas with stored data
    deltas = records.reset_index() \
        .groupby(['TimeStep']) \
        ['StartTime'].max() \
        .fillna(deltas['StartTime']) \
        .to_frame() \
        .join(deltas.EndTime)

    # Build the list of data to load / update
    toloads = []
    for ts, delta in deltas.iterrows():
        for symbol in Symbol:
            rec = records.xs((ts, symbol.name))
            if rec.EndTime is not pd.NaT:
                if rec.EndTime != delta.EndTime:
                    print(f"Update {ts} {symbol.name} from {rec.EndTime} to {delta.EndTime}")
                    toloads.append((TimeStep[ts], symbol, rec.EndTime, delta.EndTime))
            else:
                print(f"Load {ts} {symbol.name} from {delta.StartTime} to {delta.EndTime}")
                toloads.append((TimeStep[ts], symbol, delta.StartTime, delta.EndTime))

    # Trigger load in batches of len(Symbol)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for deltas in [toloads[i:i + len(Symbol)] for i in range(0, len(toloads), len(Symbol))]:
            future = executor.submit(etl_historical_klines, deltas)

