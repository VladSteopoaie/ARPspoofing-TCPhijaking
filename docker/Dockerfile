FROM snisioi/retele:2021

RUN apt-get update && apt-get install -y python3 iptables iproute2 libnetfilter-queue-dev

RUN pip3 install --upgrade python-iptables cython
RUN pip3 install loguru

RUN mkdir -p /scripts
COPY src/* /scripts/

