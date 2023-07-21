FROM ubuntu:latest

copy requirements.txt /tmp/

RUN apt-get update && apt-get install python3-pip -y && pip install -r /tmp/requirements.txt


WORKDIR /my_server/add_crypto



