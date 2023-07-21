FROM ubuntu:latest

copy requirements.txt /tmp/

RUN apt-get update && apt-get install python3-pip -y && pip install -r /tmp/requirements.txt

ADD collect_data.py /my_server/add_crypto/collect_data.py
ADD pre_process_data.py /my_server/add_crypto/pre_process_data.py
ADD start.sh /my_server/add_crypto/start.sh

WORKDIR /my_server/add_crypto

CMD ["./start.sh"]

