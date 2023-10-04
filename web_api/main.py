import os
import sys
sys.path.insert(0, os.path.abspath("../"))
sys.path.insert(0, os.path.abspath("../binance_bridge"))
from binance_bridge.schemas import Symbol, TimeStep, SymbolName
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import mysql.connector
import uvicorn
import plotly.graph_objs as go
import plotly.io.json as pjson
from plotly.subplots import make_subplots
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any
import secrets
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = b"cryptobot"
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = b"cryptic"
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

SymbolSlug = Enum('SymbolSlug', {s.name:s.name.lower() for s in Symbol})
TimeStepSlug = Enum('TimeStepSlug', {s.name:s.name.lower() for s in TimeStep})

app = FastAPI() 
app.mount("/static", StaticFiles(directory="static"), name="static")

def template_share_vars(request: Request) -> Dict[str, Any]:
    return {
        'Symbol': Symbol,
        'SymbolName': SymbolName,
        'SymbolSlug': SymbolSlug,
        'time': datetime.now()
    }

templates = Jinja2Templates(directory="templates", context_processors=[template_share_vars])
TemplateResponse = templates.TemplateResponse

def connect():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST_PREDICTIONS'),
            user=os.getenv('MYSQL_USER_PREDICTIONS'),
            password=os.getenv('MYSQL_PASSWORD_PREDICTIONS'),
            database=os.getenv('MYSQL_DATABASE_PREDICTIONS')
        )
        return conn
    except Exception as e:
        pass

def tmpl_context(request: Request) -> Dict[str, Any]:
    """Jinja template context mixin"""
    return lambda **kwargs: {**kwargs, 'request': request}

TemplateVars = Depends(tmpl_context)

@app.get('/')
def index(context = TemplateVars) -> HTMLResponse:
    """Home page
    Display the list of 1 hour ahead predictions for all symbols.
    """
    now = datetime.now()
    if now.hour < 2:
        now = now - timedelta(days=1)
    now_4days = (now + timedelta(days=4))
    dbconn = connect()
    if not dbconn:
        tmpl_vars = context(message=f"Navré, service momentanément indisponible")
        return templates.TemplateResponse("error.html", tmpl_vars, status_code=204)

    cursor = dbconn.cursor(dictionary=True)
    query = """
    SELECT KL.ClosePrice NowClosePrice, PR.*
      FROM klines KL
      LEFT JOIN predictions PR
        ON KL.Symbol = PR.Symbol AND KL.TimeStep = PR.TimeStep
     WHERE PR.TimeStep = 'DAILY'
       AND DATE(PR.OpenTime) = %s
       AND DATE(KL.OpenTime) = %s
     ORDER BY Symbol
    """
    cursor.execute(query, [now_4days.strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d')])
    datas=cursor.fetchall()
    cursor.close()
    dbconn.close()

    tmpl_vars = context(
        pred_date=now_4days,
        predictions=datas)

    return TemplateResponse('index.html', tmpl_vars)

@app.get('/forecast/{symbol}/{timestep}')
def forecast(symbol: SymbolSlug, timestep: TimeStepSlug, context = TemplateVars) -> HTMLResponse:
    dbconn = connect()
    if not dbconn:
        tmpl_vars = context(message=f"Navré, service momentanément indisponible")
        return templates.TemplateResponse("error.html", tmpl_vars, status_code=204)

    cursor = dbconn.cursor(dictionary=True)

    # Select most recent klines
    unit = dict(zip(TimeStepSlug, ['MINUTE', 'HOUR', 'DAY', 'WEEK']))[timestep]
    query = f"""
    SELECT * FROM klines
     WHERE Symbol = %s AND TimeStep = %s
       AND OpenTime >= DATE_SUB(
           (SELECT MAX(OpenTime) FROM klines
             WHERE Symbol = %s AND TimeStep = %s),
           INTERVAL 3 {unit})
     ORDER BY OpenTime
    """
    cursor.execute(query, [symbol.name, timestep.name, symbol.name, timestep.name])
    klines = cursor.fetchall()
    if len(klines) < 4:
        tmpl_vars = context(message=f"Navré, aucune données disponibles pour {symbol.name}")
        return templates.TemplateResponse("error.html", tmpl_vars, status_code=200)

    last_k = klines[-1].get('OpenTime')

    query = """
    SELECT * FROM predictions
     WHERE Symbol = %s AND TimeStep = %s
       AND OpenTime > %s
     ORDER BY OpenTime
    """
    cursor.execute(query, [symbol.name, timestep.name, last_k])
    predictions = cursor.fetchall()

    cursor.close()
    dbconn.close()

    dates = [x['OpenTime'] for x in klines] + [x['OpenTime'] for x in predictions]
    ldata = [x['ClosePrice'] for x in klines]
    rdata = [None]*(len(klines) - 1) + [klines[-1]['ClosePrice']]
    rdata = rdata + [x['ClosePrice'] for x in predictions]

    #
    unit = dict(zip(TimeStepSlug, ['M', 'H', 'J', 'S']))[timestep]

	# Compute close price variations
    variations = []
    prices = [ldata[-1]] + [x['ClosePrice'] for x in predictions]
    for i in range(len(prices) - 1):
        p = prices[i + 1]
        v = (p - prices[i]) / p
        variations.append(dict(PctChange=v, ClosePrice=p))

    txts = [None]*(len(klines)) + [unit + str(i) for i in range(1, 5)]
    fig = go.Figure(
        data = [
            go.Line(x=dates, y=ldata, line_color='orange', mode='lines+markers+text', name=''),
            go.Line(x=dates, y=rdata, text=txts, line_dash="dot", line_color='orange', mode='lines+markers+text', textposition='top right', name=''),
        ],
        layout = go.Layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin={ 't': 0, 'r': 0, 'b': 0, 'l': 0 },
            showlegend=False,
            yaxis_title=None,
            xaxis_title=None
        )
    )
    fig.update_yaxes(gridcolor='rgba(0,0,0,.1)')
    fig.update_xaxes(showgrid=False)

    plot_json = pjson.to_json_plotly(fig)

    tmpl_vars = context(
        now=datetime.now(),
        unit=unit,
        unit_word=dict(zip(TimeStepSlug, ['Minute', 'Heure', 'Jour', 'Semaine']))[timestep],
		variations=variations,
        timestep=timestep.value,
        klines=klines,
        predictions=predictions,
        symbol=symbol.name,
        plot_json=plot_json
    )
    return templates.TemplateResponse("forecast.html", tmpl_vars)

@app.get('/precision')
def precision(context = TemplateVars, credentials: HTTPBasicCredentials = Depends(security)) -> HTMLResponse:

    dbconn = connect()
    cursor = dbconn.cursor(dictionary=True)
    query = """
    SELECT K.OpenTime as 'date', K.Symbol as 'symbol', K.TimeStep as timestep, ((ABS(P.ClosePrice - K.ClosePrice) / K.ClosePrice) * 100) AS precision_rate
    FROM predictions P
    JOIN klines K ON K.OpenTime = P.OpenTime AND K.Symbol = P.Symbol AND K.TimeStep = P.TimeStep;
    """
    cursor.execute(query)
    datas = cursor.fetchall()
    cursor.close()
    dbconn.close()

    # Extraction des symboles uniques et des délais uniques
    symbols = set(entry['symbol'] for entry in datas)
    #timesteps = set(entry['timestep'] for entry in datas)

    timesteps = [ts.name for ts in TimeStep]

    # Créez une sous-figure avec Plotly
    fig = make_subplots(rows=len(symbols), cols=1, subplot_titles=timesteps)

    j = 1

    for i, timestep in enumerate(timesteps):
        for symbol in symbols:
            # Filtrer les données pour le symbole et le délai actuels
            subset = [entry for entry in datas if entry['symbol'] == symbol and entry['timestep'] == timestep]

            # Extraire les dates et les taux de précision pour le sous-graphique actuel
            dates = [entry['date'] for entry in subset]
            precision_rates = [entry['precision_rate'] for entry in subset]

            # Créer une trace de ligne avec Plotly pour le sous-graphique actuel
            trace = go.Scatter(x=dates, y=precision_rates, mode='lines+markers', name=symbol + " - " + timestep)

            # Ajouter la trace au sous-graphique correspondant
            fig.add_trace(trace, row=i+1, col=j)

        # Mettre à jour les titres des sous-graphiques
        fig.update_xaxes(title_text=None, row=i+1, col=j)
        fig.update_yaxes(title_text='Taux d\'erreur de précision', row=i+1, col=j)

    # Mettre à jour la disposition de la figure
    fig.update_layout(showlegend=True)
    fig.update_layout(height=1200)


    plot_json = pjson.to_json_plotly(fig)

    tmpl_vars = context(plot_json=plot_json)

    return TemplateResponse('precision.html', tmpl_vars)

@app.get('/model-stats')
def precision(context = TemplateVars, credentials: HTTPBasicCredentials = Depends(security)) -> HTMLResponse:
    dbconn = connect()
    cursor = dbconn.cursor(dictionary=True)

    # Signals
    query = """
    SELECT S.Symbol, S.TimeStep, S.k_signal, S.OK, COUNT(S.OK) AS OK_count FROM (
        SELECT R.*, R.k_signal = p_signal AS OK
        FROM (
            SELECT P.Symbol, P.TimeStep,
                CASE WHEN (K.ClosePrice - K.OpenPrice) >= 0 THEN 'neg' ELSE 'pos' END AS k_signal,
                CASE WHEN (P.ClosePrice - K.OpenPrice) >= 0 THEN 'neg' ELSE 'pos' END AS p_signal
            FROM predictions AS P
            JOIN klines K ON K.OpenTime = P.OpenTime AND K.Symbol = P.Symbol AND K.TimeStep = P.TimeStep
        ) AS R
    ) AS S
    GROUP BY S.Symbol, S.TimeStep, S.k_signal, S.OK
    ORDER BY S.Symbol, S.TimeStep, S.k_signal, S.OK
    """
    cursor.execute(query)
    res = cursor.fetchall()
    # return res
    signals = {ts.name: {sy.name: {'neg': 0, 'pos': 0} for sy in Symbol} for ts in TimeStep}
    for row in res:
        sig = signals[row['TimeStep']][row['Symbol']]
        sig[row['k_signal']]+= row['OK_count']

    for row in res:
        if row['OK']:
            sig = signals[row['TimeStep']][row['Symbol']]
            tot = sig[row['k_signal']]
            sig[row['k_signal']] = (row['OK_count'] / tot, tot)

    for ts in TimeStep:
        for sy in Symbol:
            sig = signals[ts.name][sy.name]
            vneg = sig['neg'][1] if isinstance(sig['neg'], tuple) else sig['neg']
            vpos = sig['pos'][1] if isinstance(sig['pos'], tuple) else sig['pos']
            sig['neg'] = (sig['neg'][0] * 100 if isinstance(sig['neg'], tuple) else 0, vneg)
            sig['pos'] = (sig['pos'][0] * 100 if isinstance(sig['pos'], tuple) else 0, vpos)
    
    # Mean errors
    query = """
    SELECT K.TimeStep as title,
           (AVG((ABS(P.ClosePrice - K.ClosePrice) / K.ClosePrice) * 100)) AS mean_error
      FROM predictions P
      JOIN klines K ON K.OpenTime = P.OpenTime AND K.Symbol = P.Symbol AND K.TimeStep = P.TimeStep
     GROUP BY K.TimeStep
     ORDER BY K.TimeStep
    """

    cursor.execute(query)
    mean_errors = cursor.fetchall()

    # Error rate
    query = """
    SELECT K.OpenTime, K.Symbol, K.TimeStep,
           ((ABS(P.ClosePrice - K.ClosePrice) / K.ClosePrice) * 100) AS PError
      FROM predictions P
      JOIN klines K ON K.OpenTime = P.OpenTime AND K.Symbol = P.Symbol AND K.TimeStep = P.TimeStep
     WHERE K.TimeStep = %s
     ORDER BY K.Symbol, K.OpenTime
    """

    plots = []
    layout = go.Layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin={ 't': 0, 'r': 0, 'b': 0, 'l': 0 },
        showlegend=False,
        yaxis_title=None,
        xaxis_title=None)

    for i, timestep in enumerate(TimeStep):
        cursor.execute(query, [timestep.name])
        res = cursor.fetchall()
        traces = []
        for symbol in Symbol:
            data = [row for row in res if row['Symbol'] == symbol.name]
            dats = [row['OpenTime'] for row in data]
            vals = [row['PError'] for row in data]
            trace = go.Scatter(x=dats, y=vals, mode='lines', name=symbol.name)
            traces.append(trace)

        fig = go.Figure(data=traces, layout=layout)
        fig.update_yaxes(gridcolor='rgba(0,0,0,.1)', title_text='% erreur pred.')
        fig.update_xaxes(showgrid=False)
        fig.update_layout(showlegend=True, height=200,
            legend=dict(yanchor="top", y=1))
        plots.append({
            'title': timestep.name,
            'json_plot': pjson.to_json_plotly(fig),
            'mean_error': mean_errors[i]['mean_error'],
            'signals': signals[timestep.name]
        })

    cursor.close()
    dbconn.close()

    tmpl_vars = context(pred_error_plots=plots)
    return TemplateResponse('model-stats.html', tmpl_vars)

# Lancer l'application FastAPI
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
