FROM python:slim

COPY data/requirements.txt .
COPY binance_bridge/requirements.txt requirements_bb.txt
RUN pip install -r requirements.txt \
 && pip install -r requirements_bb.txt

COPY data/build_history.py src/data/
COPY binance_bridge/*.py src/binance_bridge/

WORKDIR /src/data

CMD [ "python", "build_history.py" ]