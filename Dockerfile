FROM python3.11

WORKDIR /

COPY .

RUN "pip3 install -r requirements.txt"