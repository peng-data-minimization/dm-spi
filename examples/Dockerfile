FROM tubpeng/kafka-data-minimization-spi:latest

ADD example_config.yml /etc/config/worker_config.yml

ENTRYPOINT [ "python", "./run.py", "--config-path", "/etc/config/worker_config.yml"]

