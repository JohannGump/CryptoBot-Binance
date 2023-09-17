import os
import sys
import requests
import json
sys.path.insert(0, os.path.abspath("../"))
sys.path.insert(0, os.path.abspath("../binance_bridge"))
from binance_bridge.schemas import Symbol, TimeStep
import mysql.connector
from datetime import datetime
from update_klines import add_time_delta
import logging

logging.basicConfig(format='[%(asctime)s] [%(levelname)s] %(module)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

klin_conn = mysql.connector.connect(
    host=os.getenv('MYSQL_HOST_KLINES'),
    user=os.getenv('MYSQL_USER_KLINES'),
    password=os.getenv('MYSQL_PASSWORD_KLINES'),
    database=os.getenv('MYSQL_DATABASE_KLINES'),
    port="3306"
)

pred_conn = mysql.connector.connect(
    host=os.getenv('MYSQL_HOST_PREDICTIONS'),
    user=os.getenv('MYSQL_USER_PREDICTIONS'),
    password=os.getenv('MYSQL_PASSWORD_PREDICTIONS'),
    database=os.getenv('MYSQL_DATABASE_PREDICTIONS'),
    port="3306"
)

PREDICT_SERVER_HOST=os.getenv('PREDICT_SERVER_HOST', None)
if not PREDICT_SERVER_HOST:
    logging.error(f"Abort, no model server host, please define `PREDICT_SERVER_HOST` env. variable")
    exit(1)

ROOT_API = f"http://{PREDICT_SERVER_HOST}/v1/models"

def ensure_predictions_table():
    """Create MySQL predictions schema if needed."""
    cursor = pred_conn.cursor()
    query = f"""
    CREATE TABLE IF NOT EXISTS predictions (
        Symbol enum({','.join(sorted([f"'{s.name}'" for s in Symbol]))}) NOT NULL,
        TimeStep enum({','.join([f"'{t.name}'" for t in TimeStep])}) NOT NULL,
        InTime DATETIME NOT NULL,
        OpenTime DATETIME NOT NULL,
        PctChange DOUBLE NOT NULL,
        ClosePrice DOUBLE NOT NULL,
        UNIQUE INDEX idx_predictions_sto (Symbol, TimeStep, OpenTime)
    )
    """
    cursor.execute(query)
    cursor.close()

def last_forecast_time(timestep: TimeStep):
    """Returns the last forecast time."""
    with pred_conn.cursor(dictionary=True) as cursor:
        query = "SELECT MAX(OpenTime) lf_time FROM predictions WHERE TimeStep = %s"
        cursor.execute(query, [timestep.name])
        res = cursor.fetchone()
    return res.get('lf_time')

def get_sequences_bounds(timestep: TimeStep):
    """Returns klines time bounds.

    Parameters
    ----------
    timestep: TimeStep
        The timestep to get klines bounds for

    Returns
    -------
    A tuple of 2 datetime as
        (<min bound>, <max bound>)
    or (None, None) when query fails
    """
    try:
        with klin_conn.cursor() as cursor:
            query = """SELECT MIN(OpenTime) as min_time, MAX(OpenTime) AS end_time
            FROM klines WHERE TimeStep = %s"""
            cursor.execute(query, [timestep.name])
            return cursor.fetchone()
    except Exception as e:
        logging.error(f"{ts.name} can't read records from klines table. {e}")
        return (None, None)

def get_flat_sequences(timestep: TimeStep, start_time: datetime, end_time: datetime):
    """Returns data to to precess for model input.

    Returned data are bounded from start_time to end_time and ordered by
    descending symbol and open time (in this order).

    Returns
    -------
    A list of model inputs values
        [
            [<OpenPrice>, <HighPrice>, <LowPrice>, <ClosePrice>, <Volume>]
            ...
        ]
    """
    query = """
    SELECT OpenPrice, HighPrice, LowPrice, ClosePrice, Volume
      FROM klines
     WHERE TimeStep = %s AND OpenTime >= %s AND OpenTime <= %s
     ORDER BY Symbol, OpenTime
    """
    try:
        with klin_conn.cursor() as cursor:
            cursor.execute(query, [timestep.name, start_time, end_time])
            data = cursor.fetchall()
            return data
    except Exception as e:
        logging.error(f"query error: {e}")
        return False

def predict(timestep:TimeStep, inputs):
    """Triggers a prediction.

    Parameters
    ----------
    timestep: TimeStep
        The model 'type' used for inference
    inputs: list
        Data used as inputs, must match format stated in model specs

    Returns
    -------
    A list: pct changes predictions for all symbol (see model specs)
    """
    api_url = f"{ROOT_API}/{timestep.name.lower()}:predict"
    payload = json.dumps({"instances": inputs})
    response = requests.post(api_url, data=payload)
    if response.status_code == 200:
        preds = response.json()['predictions'][0]
        return preds
    else:
        logging.error(f"{ts.name} model error {response.text}")

def bulk_predict(timestep:TimeStep, start_time: datetime, end_time: datetime):
    """Triggers multiple predictions.

    Predicted times are computed within the given time range
    [start_time, end_time]. That mean the predicted range will be
    [start_time + 7 unit, end_time + 4 unit], where unit derive from timestep,
    ie: minute, hour...

    Parameters
    ----------
    timestep: TimeStep
        The model 'type' used for inference
    start_time: datetime
        Min timestamp for selected data inputs
    end_time: datetime
        MinMax timestamp for selected data inputs

    Returns
    -------
    dict of key:values pairs
    {
        <time predicted>: (<input sequences>, <raw model prediction>)
        ...
    }
    or None if one of the following appen:
    - given times bounds does not match existing klines
    - model fail on one of the prediction 
    """
    ts_tosecs = dict(zip(TimeStep, (60, 3600, 86400, 604800)))[ts]
    s_offs = int((end_time - min_time).total_seconds() // ts_tosecs) + 1
    r_seqs = get_flat_sequences(timestep, start_time, end_time)
    if r_seqs is None:
        logging.error(f"can't get {timestep.name} ({start_time}, {end_time}) klines")
        return

    # Build a dict of {<time to predict>: <input sequences>} key/value pairs
    i_seqs = {}
    t_pred = add_time_delta(min_time, ts, 7) # min time is inclusive
    for n in range(s_offs - 3):
        batch = []
        for i in range(len(Symbol)):
            ofs = (i * s_offs) + n
            seq = r_seqs[ofs:ofs + 4]
            # FIXME: monkey patch, ADA (maybe others?) Volume is sometimes 0
            for j, s in enumerate(seq):
                if s[-1] == 0:
                    seq[j] = (*s[:-1], 1e-9)
            batch.append(seq)
        i_seqs[t_pred] = batch
        t_pred = add_time_delta(t_pred, ts, 1)

    # Get forecasts for computed batches
    predictions = {}
    for t_pred, batch in i_seqs.items():
        preds = predict(timestep, batch)
        if not preds:
            return
        predictions[t_pred] = (batch, preds)

    return predictions

if __name__ == "__main__":
    ts = os.getenv('TIMESTEP', TimeStep.HOURLY.name).upper()
    if ts not in TimeStep.__members__.keys():
        logging.error(f"'{ts}' is not a valid timestep, please use one of {[t.name for t in TimeStep]}")
        exit(1)
    ts = TimeStep[ts]

    ensure_predictions_table()

    # Get klines bounds
    min_time, end_time = get_sequences_bounds(ts)
    if end_time is None:
        logging.info(f"{ts.name} empty klines, this script requires at least {len(Symbol)*4} records to succeed")
        exit(1)
    # Compare with already made predictions
    last_pred = last_forecast_time(ts)
    if last_pred is None:
        # Fresh start, no predictions was made and we have data to proceed,
        # assume inputs from min_time to end_time computed above
        pass
    else:
        # At least one prediction exists, check if we need to make new ones.
        # Abort if last prediction match most recent klines
        if add_time_delta(last_pred, ts, -4) == end_time:
            logging.info(f"{ts.name} predictions up to date, latest {last_pred}")
            exit()
        # Compute the min time bound we have to start from
        # We want to predict from the last prediction time + 1 unit to the
        # most recent kline
        min_time = add_time_delta(last_pred, ts, 1)
        min_time = add_time_delta(min_time, ts, -7) # we want last + 1 unit

    # Get forecasts for the computed range
    raw_preds = bulk_predict(ts, min_time, end_time)
    if raw_preds is None:
        # We should have something ?!!
        logging.error(f"{ts.name} can't get predictions for ({min_time}, {end_time}), abort")
        exit(1)

    # Format and insert predictions
    query = f"""
    INSERT INTO predictions
        (Symbol, TimeStep, InTime, OpenTime, PctChange, ClosePrice)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    in_time = datetime.now()
    # One prediction give percent change for all symbols, so we extract from it
    # one record per symbol and compute the close price on the fly.
    for t_pred, item in raw_preds.items():
        batch, preds = item
        recs = []
        for i, symbol in enumerate(sorted([symbol.name for symbol in Symbol])):
            syseq_last = batch[i][-1] # symbol's last sequence input
            pct_change = preds[i]
            close_price = syseq_last[-2] * (1 + pct_change) # computed close price
            recs.append([symbol, ts.name, in_time, t_pred, pct_change, close_price])
        try:
            cursor = pred_conn.cursor()
            cursor.executemany(query, recs)
            logging.info(f"{ts.name} predictions inserted for {t_pred}")
            cursor.close()
        except Exception as e:
            logging.error(f"{ts.name} query error: {e}")
            logging.info(f"{ts.name} rollback previous records state")
            pred_conn.rollback()
            exit(1)
    pred_conn.commit()