# Kafka Streaming Provider Interface ![](https://github.com/peng-data-minimization/kafka-spi/workflows/Docker%20Image%20CI/badge.svg)

Configurable Interface to apply data minimization tools on Apache Kafka topics.

## Deployment
You can use the [docker hub image](https://hub.docker.com/repository/docker/tubpeng/kafka-data-minimization-spi) to deploy the data minimization streaming provider interface. 
Copy your configuration to the container and execute `run.py`. 
```
FROM tubpeng/kafka-data-minimization-spi

COPY examples/example_config /etc/config/worker_config.yml

ENTRYPOINT [ "python", "./run.py", "--config-path", "/etc/config/worker_config.yaml"]

```

## Development
Images are build and published to docker hub.
To run outside a docker container run `python run.py --config-path YOUR_CONFIG_PATH`

## Documentation

### Configuration
The configuration is devided into three components (yaml keys). The `streaming_platform`, the `task_defaults` and finally the `tasks`. 
A sample file, covering most possible options can be found in the [examples](/examples) folder. For further documentation, see below.
#### streaming_platform
This section defines the underlying streaming platform. As of now, we only support kafka as streaming platform. We will include auth support in the future.
```
streaming_platform:
  type: {kafka}
  broker_url: "HOST:PORT"
```

#### task_defaults
This sction allows you to define defaults for all defined tasks. Note, that you can override these for specific tasks (if a value is defined both in `task_defaults` and in the `task` description, the worker will use the value from the `task` description). You can set a default for every `task` parameter.
```
task_defaults:
  input_offset_reset: {earliest, latest}
  topic_encoding: MUST BE A PYTHON COMPATIBLE ENCODING
  storage_mode: {memory, persistent}
  input_data_type: {}

```

### task
This section defines the tasks that are executed by the worker. 
For more information of the data minimization api see [here](https://github.com/peng-data-minimization/minimizer).

```
tasks:
- name: first
  input_topic: "foo"
  output_topic: "bar"
  function:
    name: FUNCTION NAME FROM THE MINIMIZATION API
    args:
      ADDITIONAL ARGUMENTS FOR MINIMIZER FUNCTION

    # for all functions that require multiple records (such as reduce_to_mean) you can define the caching window as follows.
    window:
      type: {length, ingestion_time}
      value: {# of items, time in seconds}
      
      # you cann add grouping keys in order to apply the function on groups on value individually.
      grouping_keys: ['b']

- name: ...
```
