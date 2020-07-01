# Kafka Streaming Provider Interface
Configurable Interface to apply data minimization tools on Apache Kafka topics.

## Hello World
To start the worker locally run 

`docker build --tag kafka_spi_worker . && docker run kafka_spi_worker`

If you are unsing a local kafka deployment, run 

`docker build --tag kafka_spi_worker . && docker run --net=host kafka_spi_worker`