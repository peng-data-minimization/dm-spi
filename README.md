# Data Minimization Streaming Provider Interface ![](https://github.com/peng-data-minimization/kafka-spi/workflows/Docker%20Image%20CI/badge.svg)

Configurable Interface to apply data minimization tools on Streaming pipelines. Currently supporting implementations for 
* Apache Kafka

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

## Configuration
The configuration is devided into three components (yaml keys). The `streaming_platform`, the `task_defaults` and finally the `tasks`. 
A sample file, covering most possible options can be found in the [examples](/examples) folder. For further documentation, see below.

### streaming_platform
This section defines the underlying streaming platform. As of now, we only support kafka as streaming platform. We will include auth support in the future.
```
streaming_platform:
  type: {kafka}
  broker_url: "HOST:PORT"
```

### task_defaults
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

## Latency Testing

To test any task configuration for latency introduced by the data minimization functions, simply switch the `provider` to `kafka-testing` and provide a file with realistic test data send to kafka. Optionally provide further configuration for the latency test:
```
streaming_platform:
  type: kafka-testing
  example_message_file: </path/to/example/message/file.json>
  test_iterations: <number of latency test iterations>
  send_timeout: <timeout in s for kafka worker sending example data>
  poll_timeout: <timeout in s for kafka consumer waiting for example data (should be significantly higher than expected latency)>
  outlier_rejecting_n_std: <number of standard deviations for which single latency measurements are considered an outlier and are being removed (set to 0 to not remove any measurements)>
```

The latency test results are being stored as `latency-summary.log` and a summary with 50, 99 and 99.9 percentiles is being logged to `INFO`.

To run the latency tests locally, just run `docker-compose up` which uses the `example_testing_config.yml`.