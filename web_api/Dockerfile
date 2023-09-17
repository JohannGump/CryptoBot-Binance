FROM python:slim

ENV TZ=Europe/Paris
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y tzdata

COPY web_api/requirements.txt /app/
RUN pip install -r /app/requirements.txt

COPY web_api/main.py /app/
COPY web_api/templates /app/templates
COPY web_api/static /app/static

WORKDIR /app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]