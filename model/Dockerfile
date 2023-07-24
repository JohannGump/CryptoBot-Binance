FROM python:slim

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY model/*.py src/model/
COPY binance_bridge/*.py src/binance_bridge/

WORKDIR /src/model

CMD [ "python", "train.py" ]