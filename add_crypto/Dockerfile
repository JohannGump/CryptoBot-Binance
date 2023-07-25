FROM ubuntu:latest

COPY requirements.txt /tmp/

RUN apt-get update && apt-get install python3-pip -y && pip install -r /tmp/requirements.txt

ADD collect_data.py /src/add_crypto/collect_data.py
ADD pre_process_data.py /src/add_crypto/pre_process_data.py
ADD configuration.py /src/add_crypto/configuration.py
ADD custo_functions.py /src/add_crypto/custo_functions.py
ADD start.sh /src/add_crypto/start.sh

RUN chmod +x /src/add_crypto/start.sh

WORKDIR /src/add_crypto

CMD ["./start.sh"]

