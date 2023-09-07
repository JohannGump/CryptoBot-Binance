FROM python:slim

ENV TZ=Europe/Paris
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y tzdata

COPY requirements.txt /app/
COPY main.py /app/
COPY templates /app/templates
COPY static /app/static

WORKDIR /app
RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]