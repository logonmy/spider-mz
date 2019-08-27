# -*- coding:utf-8 -*-
from kafka import KafkaProducer
import json


class KafkaProducerUtils(object):
    def __init__(self, server, topic):
        self.server = server
        self.topic = topic
        # kafka-broker 地址
        self.producer2 = KafkaProducer(bootstrap_servers=['127.0.0.1:9092'],
                                       value_serializer=lambda m: json.dumps(m).encode('utf-8'))

    def producer(self, message):
        self.producer2.send('test-topic', message)


    def close(self):
        self.producer2.close()

if __name__ == '__main__':
    producer1 = KafkaProducerUtils('', '')
    producer1.producer({'key':'送快递快放假'})