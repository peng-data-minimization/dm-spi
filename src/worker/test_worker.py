from confluent_kafka import Consumer
from kafka.errors import KafkaTimeoutError
from worker.kafka_worker import KafkaWorker
import numpy as np
import argparse
import threading
import time
import json
import os

class TestKafkaWorker(KafkaWorker):
    POLL_TIMEOUT_DEFAULT = 25
    SEND_TIMEOUT_DEFAULT = 5
    TEST_ITERATIONS_DEFAULT = 100
    OUTLIER_REJECTING_N_STD = 2


    def __init__(self, platform_config, tasks):
        super().__init__(platform_config, tasks)
        self.poll_timeout = getattr(self.platform_config, 'poll_timeout', self.POLL_TIMEOUT_DEFAULT)
        self.send_timeout = getattr(self.platform_config, 'send_timeout', self.SEND_TIMEOUT_DEFAULT)
        self.test_iterations = getattr(self.platform_config, 'test_iterations', self.TEST_ITERATIONS_DEFAULT)
        self.outlier_rejecting_n_std = getattr(self.platform_config, 'outlier_rejecting_n_std', self.OUTLIER_REJECTING_N_STD)
        self.example_message_file = getattr(self.platform_config, 'example_message_file', None)
        if self.example_message_file is None:
            raise Exception("Missing configuration. Please provide an 'streaming_platform.example_message_file' to be used in latency tests.")


    def init_consumer(self, task):
        consumer = Consumer({
                'bootstrap.servers': self.platform_config.broker_url,
                'group.id': 'mygroup',
                'auto.offset.reset': 'earliest',
            })

        # make testing worker write data to the spi input topic and consume from the output topic
        consumer.subscribe([task.output_topic])
        return consumer


    def test_task(self, task):
        self.logger.info(f'Testing task {task.name}...')

        self.consumer = self.init_consumer(task)
        self.producer = self.init_producer(task)

        self.latency_test(task)


    def latency_test(self, task):
        self.logger.info(f'Starting latency test for task {task.name}...')
        latencies = []
        msg = self._get_message()

        for _ in range(self.test_iterations):
            latencies.append(self._latency_iteration(task, msg))

        self._persist_test_results(latencies, task.name)


    def _latency_iteration(self, task, msg_send):
        try:
            record_metadata = self.send(self.producer, msg_send, task.input_topic)
            self.producer.flush(self.send_timeout)
        except KafkaTimeoutError:
            self.logger.warning('Aborting latency test due to timed out sending of records.')
            return

        start = time.perf_counter()

        msg_rec = self.consumer.poll(self.poll_timeout)
        if msg_rec is None:
            raise Exception(f'Consumer timeout reached when polling ({self.poll_timeout}s)')
        if msg_rec.error():
            raise Exception(f'Consumer error when polling: {msg_rec.error()}')
        latency = time.perf_counter() - start
        self.logger.debug(f'Successfully received record - topic: {msg_rec.topic()}, partition: {msg_rec.partition()}, offset: {msg_rec.offset()}')

        self._validate_message_consistency(msg_send, msg_rec, record_metadata)

        return latency


    def _persist_test_results(self, latencies, task_name):
        a = np.array(latencies)
        # reject outliers e.g. first iteration is always a lot slower
        a = self._reject_outliers(a, n_std=self.outlier_rejecting_n_std)
        np.savetxt(f'{task_name}-latencies.log', a, newline='\n')
        self.logger.info('#### LATENCY TEST RESULTS ####')
        self.logger.info(f'50 percentile: {np.percentile(a, 50)}')
        self.logger.info(f'99 percentile: {np.percentile(a, 99)}')
        self.logger.info(f'99.9 percentile: {np.percentile(a, 99.9)}')


    def _validate_message_consistency(self, msg_send, msg_rec, record_metadata):
        # data minimization will potentially change message attributes, check for untouched attribute instead
        if msg_send.get('foo') != json.loads(msg_rec.value()).get('foo'):
            raise Exception(f"Message send and received are different: {msg_send.get('id')} vs. {json.loads(msg_rec.value()).get('id')} (send message offset {self._get_offset(record_metadata)} & received message offset {msg_rec.offset()})")


    def _get_offset(self, record_metadata):
        return getattr(record_metadata.value,'offset')


    def _get_message(self):
        if not os.path.exists(self.example_message_file):
            self.logger.error(f'Example message file for latency tests does not exist ({self.example_message_file}).')
            return {}
        with open(self.example_message_file, 'r') as file:
            return json.load(file)


    def _reject_outliers(self, data, n_std=2):
        # reject outliers based on number of standard deviations around mean
        data = data[data != np.array(None)]
        if len(data) > 0:
            return data[abs(data - np.mean(data)) < n_std * np.std(data)]
        return data


    def run(self):
        # start actual kafka worker to be tested
        self.logger.info('Starting the kafka spi worker which is to be tested...')
        worker = KafkaWorker(self.platform_config, self.tasks)
        worker_thread = threading.Thread(target=worker.run)
        worker_thread.start()
        self.logger.info('Kafka spi worker started in thread.')

        for task in self.tasks:
            self.logger.info(f"Started tests for task {task.name}")
            self.test_task(task)
