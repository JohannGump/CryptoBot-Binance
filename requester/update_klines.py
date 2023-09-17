import os
import sys
import requests
from datetime import datetime, timedelta
import mysql.connector
sys.path.insert(0, os.path.abspath("../"))
sys.path.insert(0, os.path.abspath("../binance_bridge"))
from binance_bridge.schemas import Symbol, TimeStep
import concurrent.futures
import asyncio
import logging

logging.basicConfig(format='[%(asctime)s] [%(levelname)s] %(module)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

connection_params = dict(
    host=os.getenv('MYSQL_HOST_KLINES'),
    user=os.getenv('MYSQL_USER_KLINES'),
    password=os.getenv('MYSQL_PASSWORD_KLINES'),
    database=os.getenv('MYSQL_DATABASE_KLINES'),
    port="3306"
)

def db_connect():
    """Returns db connection"""
    return mysql.connector.connect(**connection_params)

def add_time_delta(curtime:datetime, interval: TimeStep, delta: int = -4):
    """Substract units of time from a datetine according to a given TimeStep.
    Note: by default we substract -4"""
    param = dict(zip(TimeStep, ['minutes', 'hours', 'days', 'weeks']))[interval]
    param = {param: delta}
    return curtime + timedelta(**param)

def get_binance_klines(symbol: Symbol, interval: TimeStep,
    start_time: datetime, end_time: datetime):
    """Load klines data from Binance.

    Returns
    -------
    A list of tuples in the form
        (<symbol>, <timestep>, <OpenTime>, <OpenPrice>, <HighPrice>, <LowPrice>, <ClosePrice>, <Volume>)
    """
    endpoint = "https://data-api.binance.vision/api/v3/klines"
    params = {
        "symbol": symbol.name,
        "interval": interval.value,
        "startTime": int(start_time.timestamp()*1000),
        "endTime": int(end_time.timestamp()*1000)
    }

    response = requests.get(endpoint, params=params)
    if response.status_code == 200:
        data = response.json()
    else: 
        logging.error(f"{symbol.name} Binance request error: {response.text}")
        return None

    formatted_data = []
    for entry in data:
        open_time = datetime.fromtimestamp(entry[0] / 1000.0)
        open_price = float(entry[1])
        high_price = float(entry[2])
        low_price = float(entry[3])
        close_price = float(entry[4])
        volume = float(entry[5])

        formatted_data.append((symbol.name, interval.name, open_time, open_price, high_price, low_price, close_price, volume))

    return formatted_data

def bulk_load_klines(ts, start_time, end_time):
    """Concurently loads klines for all symbols.
    """
    async def load(symbol, ts, start_time, end_time):
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None,
            lambda: get_binance_klines(symbol, ts, start_time, end_time))
        return data

    async def run():
        futures = []
        for symbol in Symbol:
            futures.append(load(symbol, ts, start_time, end_time))
        recs = await asyncio.gather(*futures)
        return recs

    return asyncio.run(run())

def insert_data_into_db(data, connection) -> bool:
    """Insert klines records.

    Transation is not commited, it's up to you to commit or rollback with
    the given connection from outside this function. Use return signal to apply
    or discard the transaction.

    Parameters
    ----------
    data: list
        A list of tuples in the form
        (<symbol>, <timestep>, <OpenTime>, <OpenPrice>, <HighPrice>, <LowPrice>, <ClosePrice>, <Volume>)
    connection: MySQLConnection
        Connection to mysql host
    
    Returns
    -------
    flag indicating success or failure of the transaction.
    """
    cursor = connection.cursor()
    syts = f"{data[0][0]} {data[0][1]}" # 'Symbol Timestep' values
    try:
        insert_query = """
        INSERT INTO klines (Symbol, TimeStep, OpenTime, OpenPrice, HighPrice, LowPrice, ClosePrice, Volume)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.executemany(insert_query, data)
        logging.info(f"{syts} {len(data)} records inserted ({data[0][2]} to {data[-1][2]})")
        return True
    except Exception as e:
        logging.error(f"{syts} insert error: {e}")
        return False
    finally:
        cursor.close()

def ensure_klines_table():
    """Create MySQL klines schema if needed.
    TODO: query error handling
    """
    cnx = db_connect()
    cursor = cnx.cursor()
    query = f"""
    CREATE TABLE IF NOT EXISTS klines (
        Symbol enum({','.join(sorted([f"'{s.name}'" for s in Symbol]))}) NOT NULL,
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
    cursor.execute(query)
    cursor.close()
    cnx.close()

if __name__ == "__main__":
    ts = os.getenv('TIMESTEP', TimeStep.HOURLY.name).upper()
    if ts not in TimeStep.__members__.keys():
        logging.error(f"'{ts}' is not a valid timestep, please use one of {[t.name for t in TimeStep]}")
        exit(1)
    ts = TimeStep[ts]

    ensure_klines_table()

    # We must ensure consistency in continuity across symbols timestamps.
    # Below computes how many samples we should have per symbols depending on
    # the presence of past data or not.

    # Clean <now> time according to binance timestamp specs
    end_time = datetime.now().replace(second=0, microsecond=0)
    # We can't have daily samples before 2:00 AM
    if ts is TimeStep.DAILY and end_time.hour < 2:
        end_time = end_time - timedelta(days=1)
    # We can't have minutely samples for minute being (not all symbols)
    if ts is TimeStep.MINUTELY:
        end_time = end_time - timedelta(minutes=1)
    else:
        end_time = end_time.replace(minute=0)
    # Daily and weekly samples are timestamped 2:00 AM
    if ts in [TimeStep.DAILY, TimeStep.WEEKLY]:
        end_time = end_time.replace(hour=2)
    # Adjust on monday for weekly
    if ts is TimeStep.WEEKLY:
        end_time = end_time - timedelta(days=end_time.weekday())

    # Computes start time
    # Where start time is :
    # <now> minus amount of sample neeeded to make 4 predictions ahead
    # or
    # <now> minus most recent past data
    # WARN: we assume that our DB is up to date with the same most recent timestamp
    # for all symbols

    start_time = None
    with db_connect() as cnx:
        query = "SELECT MAX(OpenTime) LastOpenTime  FROM klines WHERE TimeStep = %s"
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(query, [ts.name])
        start_time = cursor.fetchone().get('LastOpenTime', None)

    if start_time is None:
        # No past data, ensuring we could have at least data to make 4
        # predictions ahead.
        mpw = max(int(os.getenv('MIN_PREDICT_WINDOW', 4)), 4)
        delta = mpw*2 - 2
        start_time = add_time_delta(end_time, ts, -delta)
    else:
        # Ensure we fill gap between now and our past data.
        start_time = add_time_delta(start_time, ts, 1)
        ts_sec = dict(zip(TimeStep, (60, 3600, 86400, 604800)))[ts]
        delta = (end_time - start_time).total_seconds() // ts_sec

    if delta < 0:
        logging.info(f"{ts.name} up to date, most recent: ({end_time})")
        exit(0)

    # Data loading, care that we must have the same number / timestamps
    # for all symbols, if one of symbol's data is diverging, we discard all.

    # Adjust delta to be inclusive of start_time (+1), limits delta to 500 samples
    # per symbol (max. records given by Binance)
    delta = min(delta + 1, 500)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(bulk_load_klines, ts, start_time, end_time)
        batches = future.result()

    # Check consistency across symbols data (amount, timestamps bounds)
    for klines in batches:
        if klines is None:
            logging.error(f"{ts.name} empty records ({start_time} {end_time} - delta: {delta})")
            exit(1)
        if len(klines) != delta:
            logging.error(f"{klines[0][0]} {ts.name} records count {len(klines)} does not match delta {delta} ({start_time} {end_time})")
            exit(1)
    bounds = [[ks[0][2], ks[-1][2]] for ks in batches]
    for bd in bounds[1:]:
        if bd != bounds[0]:
            logging.error("%s %s times bounds (%s %s) differ from (%s, %s)" % (
                klines[0][0],
                ts.name,
                bd[0].strftime('%Y-%m-%d %H:%M'),
                bd[1].strftime('%Y-%m-%d %H:%M'),
                bounds[0][0].strftime('%Y-%m-%d %H:%M'),
                bounds[0][1].strftime('%Y-%m-%d %H:%M')))  
            exit(1)

    # Store
    connection = db_connect()
    for klines in batches:
        if not insert_data_into_db(klines, connection):
            connection.rollback()
            logging.info("rollback previous records state")
            exit(1)
    connection.commit()