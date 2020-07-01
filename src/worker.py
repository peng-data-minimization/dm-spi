from kafka import KafkaProducer, KafkaConsumer
from utils.config_parser import parse_config
import argparse
from utils import get_value_deserializer, get_logger
import threading
import _temp_data_minimization_tools as dmt
from window import Window
import json
from storage import StorageModes

logger = get_logger()


def process_consumer(consumer, task, window):
    for msg in consumer:
        try:
            encoded_msg = msg.value.decode(task.topic_encoding)
        except UnicodeDecodeError:
            logger.warning(f"Could not decode message {msg.value} with encoding {task.topic_encoding}. Skipping.")
            continue
        try:
            deserialized_obj = get_value_deserializer(task.input_data_type)(encoded_msg)
        except:
            logger.warning(f"could not deserialize message {encoded_msg}. "
                           f"Provided input data type: {task.input_data_type}. Skipping.")
            continue
        logger.debug(f"recieved message: {encoded_msg}")
        window.add_to_window(deserialized_obj.copy())
        logger.debug("added message to window")

        if window.stop_crit_applies():
            keys, window_groups = window.return_window_data()
            processed_data = []
            for key, group in zip(keys, window_groups):
                logger.info(f"processing group for key {key} (length: {len(group)}) "
                            f"with function {task.function['signature']}")
                logger.debug(f"Group: {group}")
                func = getattr(dmt, task.function['signature'])
                processed_data.extend(func(group, **task.function['args']))

            yield processed_data


def task_thread(task, streaming_platform_config):
    if hasattr(task, 'input_offset_reset') and task.input_offset_reset:
        offset_reset = task.input_offset_reset
    else:
        offset_reset = 'latest'
    
    consumer = KafkaConsumer(bootstrap_servers=streaming_platform_config.broker_url, auto_offset_reset=offset_reset)

    consumer.subscribe([task.input_topic])
    producer = KafkaProducer(bootstrap_servers=streaming_platform_config.broker_url,
                             value_serializer=lambda v: json.dumps(v).encode(task.topic_encoding))

    window_config = task.function.get('window')
    window_id = f"{task.name.replace(' ', '')}"
    if not window_config:
        window = Window(Window.StopCrits.SINGLE_RECORD, window_id=window_id,
                        storage_mode=getattr(StorageModes, task.storage_mode.upper()))
    else:
        window = Window(getattr(Window.StopCrits, window_config['type'].upper()), stop_value=window_config['value'],
                        group_by_keys=window_config.get('grouping_keys'), window_id=window_id,
                        storage_mode=getattr(StorageModes, task.storage_mode.upper()))

    for msgs in process_consumer(consumer, task, window):
        for msg in msgs:
            logger.debug(f"sending message: {msg}")
            producer.send(task.output_topic, msg)
        producer.flush()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SPI worker for Apache Kafka.')
    parser.add_argument('--config_path', required=True, help='the path to the config.yml file.')
    args = parser.parse_args()

    streaming_platform_config, tasks = parse_config(args.config_path)
    logger.info("parsed config")
    logger.debug(streaming_platform_config)
    logger.debug(tasks)
    worker_threads = []

    for task in tasks:
        worker_thread = threading.Thread(target=task_thread, args=(task, streaming_platform_config))
        worker_threads.append(worker_thread)
        worker_thread.start()
        logger.info(f"started thread for task {task.name}")

    for thread in worker_threads:
        thread.join()
