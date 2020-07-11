from utils import get_value_deserializer, get_logger
import threading
import data_minimization_tools as dmt
from utils.window import Window

from utils.storage import StorageModes
from abc import ABC, abstractmethod


class BaseWorker(ABC):
    def __init__(self, platform_config, tasks):
        self.logger = get_logger()
        self.platform_config = platform_config
        self.tasks = tasks

    @abstractmethod
    def init_consumer(self, task):
        pass

    @abstractmethod
    def init_producer(self, task):
        pass

    @abstractmethod
    def consume_iter(self, consumer):
        pass

    @abstractmethod
    def send(self, producer, message, target):
        pass

    def process_consumer(self, consumer, task, window):
        self.logger.info(f'Start consuming and processing kafka messages...')
        for msg in self.consume_iter(consumer):
            self.logger.debug(f'Consuming message {msg}')
            try:
                encoded_msg = msg.value.decode(task.topic_encoding)
            except UnicodeDecodeError:
                self.logger.warning(
                    f"Could not decode message {msg.value} with encoding {task.topic_encoding}. Skipping.")
                continue
            try:
                deserialized_obj = get_value_deserializer(task.input_data_type)(encoded_msg)
            except:
                self.logger.warning(f"could not deserialize message {encoded_msg}. "
                                    f"Provided input data type: {task.input_data_type}. Skipping.")
                continue
            self.logger.debug(f"received message: {encoded_msg}")
            window.add_to_window(deserialized_obj.copy())
            self.logger.debug("added message to window")

            if window.stop_crit_applies():
                keys, window_groups = window.return_window_data()
                processed_data = []
                for key, group in zip(keys, window_groups):
                    self.logger.info(f"processing group for key {key} (length: {len(group)}) "
                                     f"with function {task.function['name']}")
                    self.logger.debug(f"Group: {group}")
                    func = getattr(dmt, task.function['name'])
                    processed_data.extend(func(group, **task.function['args']))

                yield processed_data

    def task_thread(self, task):
        consumer = self.init_consumer(task)
        producer = self.init_producer(task)

        window_config = task.function.get('window')
        window_id = f"{task.name.replace(' ', '')}"
        if not window_config:
            window = Window(Window.StopCrits.SINGLE_RECORD, window_id=window_id,
                            storage_mode=getattr(StorageModes, task.storage_mode.upper()))
        else:
            window = Window(getattr(Window.StopCrits, window_config['type'].upper()), stop_value=window_config['value'],
                            group_by_keys=window_config.get('grouping_keys'), window_id=window_id,
                            storage_mode=getattr(StorageModes, task.storage_mode.upper()))

        for msgs in self.process_consumer(consumer, task, window):
            for msg in msgs:
                self.logger.debug(f"sending message: {msg}")
                self.send(producer, msg, task.output_topic)

    def run(self):
        worker_threads = []
        for task in self.tasks:
            worker_thread = threading.Thread(target=self.task_thread, args=(task, ))
            worker_threads.append(worker_thread)
            worker_thread.start()
            self.logger.info(f"started thread for task {task.name}")

        for thread in worker_threads:
            thread.join()
