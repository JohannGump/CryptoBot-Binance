FROM python:slim

#ENV
ENV TZ=Europe/Paris
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y tzdata

# Install the required Python modules using pip mysql-connector-python
COPY requester/requirements.txt /app/
RUN pip install -r /app/requirements.txt 

# Copy in the container
COPY binance_bridge/schemas.py /binance_bridge/schemas.py
COPY requester/update_klines.py /app/
COPY requester/predict.py /app/
COPY requester/entrypoint.sh /app/
COPY requester/etl-and-predict.sh /app/
COPY fake-cron.sh /fake-cron.sh

# Donner les permissions d'exécution au script shell et cmd python
RUN chmod +x /app/entrypoint.sh
RUN chmod +x /app/etl-and-predict.sh
RUN chmod +x /fake-cron.sh

# Define working folder
WORKDIR /app

# Execute python script
ENTRYPOINT ["/app/entrypoint.sh"]