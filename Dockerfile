FROM python:3.8

COPY src/ /

RUN pip install -r requirements.txt


