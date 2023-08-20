from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import mysql.connector
import uvicorn
import plotly.graph_objs as go
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

#connect to db
db = mysql.connector.connect(
    host="db_predict", 
    user="root",
    password="password",
    database="predictions_history"
)

@app.get("/", response_class=HTMLResponse)
def get_home(request: Request):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM predictions ORDER BY Datetime")
    results = cursor.fetchall()
    cursor.close()

    ada_values = [result[0] for result in results]
    bnb_values = [result[1] for result in results]
    btc_values = [result[2] for result in results]
    eth_values = [result[3] for result in results]
    xrp_values = [result[4] for result in results]
    dates = [result[5] for result in results]

    # Créez les traces pour chaque paire de dates et de valeurs
    trace_ada = go.Scatter(x=dates, y=ada_values, name='ADAUSDT')
    trace_bnb = go.Scatter(x=dates, y=bnb_values, name='BNBUSDT')
    trace_btc = go.Scatter(x=dates, y=btc_values, name='BTCUSDT')
    trace_eth = go.Scatter(x=dates, y=eth_values, name='ETHUSDT')
    trace_xrp = go.Scatter(x=dates, y=xrp_values, name='XRPUSDT')

    data = [trace_ada, trace_bnb, trace_btc, trace_eth, trace_xrp]

    layout = go.Layout(
        title='Évolution des prédictions',
        xaxis=dict(title='Date', tickformat='%Y-%m-%d %H:%M:%S'),
        yaxis=dict(title='Valeur de prédiction')
    )

    fig = go.Figure(data=data, layout=layout)

    graph_html = fig.to_html(full_html=False, default_height=500, default_width=700)

    return templates.TemplateResponse("index.html", {"request": request, "graph_html": graph_html})

@app.post("/predictions", response_class=JSONResponse)
async def get_predictions(request: Request, latest_prediction: list = Form([])):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM predictions ORDER BY Datetime DESC LIMIT 1")
    latest_prediction = cursor.fetchone()
    cursor.close()
    return {"latest_prediction": latest_prediction}

# Lancer l'application FastAPI
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)