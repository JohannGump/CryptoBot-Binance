FROM python:slim

#ENV
ENV TZ=Europe/Paris
ENV DEBIAN_FRONTEND=noninteractive

# Copy in the container
COPY schemas.py /app/
COPY main.py /app/
COPY preprocessing.py /app/
COPY cronjob /etc/cron.d/cronjob
COPY entrypoint.sh /app/
COPY create-klines.sh /app/
COPY predict.py /app/
COPY requirements.txt /app/
COPY .env /app/

# Define working folder
WORKDIR /app

# Install the required Python modules using pip mysql-connector-python
RUN pip3 install datetime -r requirements.txt 

# Install cron
RUN apt-get update && apt-get install -y cron tzdata nano python3-pip

# Create log file
RUN touch /var/log/cron.log

# Donner les permissions d'exécution au script shell et cmd python
RUN chmod +x /app/entrypoint.sh
RUN chmod +x /app/create-klines.sh
RUN chmod +x /app/main.py
RUN chmod +x /app/preprocessing.py
RUN chmod +x /app/predict.py

# Give right permissions to configuration cron file
RUN chmod 0644 /etc/cron.d/cronjob

# Apply cron job configuration
RUN crontab /etc/cron.d/cronjob

# Execute python script and cron
ENTRYPOINT ["/app/entrypoint.sh"]