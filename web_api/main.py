import os
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import mysql.connector
import uvicorn
import plotly.graph_objs as go
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any

class Symbol(str, Enum):
    ADAUSDT = "ADA"
    BTCUSDT = "BTC"
    BNBUSDT = "BNB"
    ETHUSDT = "ETH"
    XRPUSDT = "XRP"

class SymbolName(str, Enum):
    ADAUSDT = "Cardano"
    BTCUSDT = "Bitcoin"
    BNBUSDT = "BNB"
    ETHUSDT = "Ethereum"
    XRPUSDT = "Ripple"

class Frequency(str, Enum):
    MINUTELY = "minutely"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"

app = FastAPI() 
app.mount("/static", StaticFiles(directory="static"), name="static")

def template_share_vars(request: Request) -> Dict[str, Any]:
    return {'Symbol': Symbol, 'SymbolName': SymbolName, 'time': datetime.now() }

templates = Jinja2Templates(directory="templates", context_processors=[template_share_vars])
TemplateResponse = templates.TemplateResponse

def connect():
    conn = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST_PREDICTIONS'),
        user=os.getenv('MYSQL_USER_PREDICTIONS'),
        password=os.getenv('MYSQL_PASSWORD_PREDICTIONS'),
        database=os.getenv('MYSQL_DATABASE_PREDICTIONS')
    )
    return conn

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
def forecast(symbol: Symbol, timestep: Frequency, context = TemplateVars) -> HTMLResponse:
    dbconn = connect()
    cursor = dbconn.cursor(dictionary=True)

    # Select most recent klines
    unit = dict(zip(Frequency, ['MINUTE', 'HOUR', 'DAY', 'WEEK']))[timestep]
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
    last_k = klines[-1].get('OpenTime')

    query = """
    SELECT * FROM predictions
     WHERE Symbol = %s AND TimeStep = %s
       AND OpenTime > %s
    """
    cursor.execute(query, [symbol.name, timestep.name, last_k])
    predictions = cursor.fetchall()

    cursor.close()
    dbconn.close()

    dates = [x['OpenTime'] for x in klines] + [x['OpenTime'] for x in predictions]
    ldata = [x['ClosePrice'] for x in klines]
    rdata = [None]*(len(klines) - 1) + [klines[-1]['ClosePrice']]
    rdata = rdata + [x['ClosePrice'] for x in predictions]

    fig = go.Figure(
        data = [
            go.Line(x=dates, y=ldata, line_color='orange', mode='lines+markers', name=''),
            go.Line(x=dates, y=rdata, line_dash="dot", line_color='orange', mode='lines+markers', name=''),
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

    graph_html = fig.to_html(full_html=True, config = {'displayModeBar': False})

    tmpl_vars = context(
        now=datetime.now(),
        unit=dict(zip(Frequency, ['M', 'H', 'J', 'S']))[timestep],
        unit_word=dict(zip(Frequency, ['Minute', 'Heure', 'Jour', 'Semaine']))[timestep],
        timestep=timestep.value,
        klines=klines,
        predictions=predictions,
        symbol=symbol.name,
        graph_html=graph_html
    )
    return templates.TemplateResponse("forecast.html", tmpl_vars)

# Lancer l'application FastAPI
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)