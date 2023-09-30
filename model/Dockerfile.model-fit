FROM python:slim

COPY model/requirements.txt .
RUN pip install -r requirements.txt

COPY binance_bridge/*.py src/binance_bridge/
COPY model/*.py src/model/
COPY model/train_models.sh src/model/
RUN chmod +x src/model/train_models.sh

WORKDIR /src/model

CMD [ "./train_models.sh" ]