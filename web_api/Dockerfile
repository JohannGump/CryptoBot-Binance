FROM python:slim

WORKDIR /app

COPY requirements.txt /app/
COPY main.py /app/
COPY templates /app/templates
COPY static /app/static

RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y nano

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]