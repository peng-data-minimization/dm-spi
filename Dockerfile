FROM python:3.8

COPY src/ /

COPY config/ /config

RUN pip install -r requirements.txt

CMD [ "python", "./worker.py", "--config_path", "config/example_config.yml" ]

