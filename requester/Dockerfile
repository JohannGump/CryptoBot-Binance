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

# Define working folder
WORKDIR /app

# Install the required Python modules using pip
RUN pip3 install requests datetime mysql.connector

# Install cron
RUN apt-get update && apt-get install -y cron tzdata nano python3-pip

# Create log file
RUN touch /var/log/cron.log

# Donner les permissions d'exécution au script shell et cmd python
RUN chmod +x /app/entrypoint.sh
RUN chmod +x /app/create-klines.sh
RUN chmod +x /app/main.py
RUN chmod +x /app/preprocessing.py

# Give right permissions to configuration cron file
RUN chmod 0644 /etc/cron.d/cronjob

# Apply cron job configuration
RUN crontab /etc/cron.d/cronjob

# Install Python dependencies
RUN pip install requests mysql-connector-python

# Execute python script and cron
ENTRYPOINT ["/app/entrypoint.sh"]