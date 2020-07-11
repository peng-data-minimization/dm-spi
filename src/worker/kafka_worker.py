from kafka import KafkaProducer, KafkaConsumer
from worker.base_worker import BaseWorker
import json


class KafkaWorker(BaseWorker):
    def init_consumer(self, task):
        self.logger.info(f'Connecting to kafka consumer @ {self.platform_config.broker_url}')
        consumer = KafkaConsumer(bootstrap_servers=self.platform_config.broker_url)
        consumer.subscribe([task.input_topic])
        self.logger.info(f'Kafka consumer subscripted to {task.input_topic}')
        return consumer

    def send(self, producer: KafkaProducer, message, target):
        return producer.send(target, message).add_callback(self.on_send_success).add_errback(self.on_send_error)

    def consume_iter(self, consumer: KafkaConsumer):
        return consumer

    def init_producer(self, task):
        producer = KafkaProducer(bootstrap_servers=self.platform_config.broker_url,
                                 value_serializer=lambda v: json.dumps(v).encode(task.topic_encoding))

        return producer

    def on_send_success(self, record_metadata):
        self.logger.debug(
            f'Successfully send record - topic: {record_metadata.topic}, partition: {record_metadata.partition}, offset: {record_metadata.offset}')


    def on_send_error(self, excp):
        self.logger.error('Failed to send record:', exc_info=excp)
