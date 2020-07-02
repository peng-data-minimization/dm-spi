from kafka import KafkaProducer, KafkaConsumer
from worker.base_worker import BaseWorker
import json


class KafkaWorker(BaseWorker):
    def init_consumer(self, task):
        consumer = KafkaConsumer(bootstrap_servers=self.platform_config.broker_url)
        consumer.subscribe([task.input_topic])
        return consumer

    def send(self, producer: KafkaProducer, message, target):
        producer.send(target, message)

    def consume_iter(self, consumer: KafkaConsumer):
        return consumer

    def init_producer(self, task):
        producer = KafkaProducer(bootstrap_servers=self.platform_config.broker_url,
                                 value_serializer=lambda v: json.dumps(v).encode(task.topic_encoding))

        return producer
