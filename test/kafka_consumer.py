# -*- coding:utf-8 -*-
from kafka import KafkaConsumer


def consumer_demo():
    consumer = KafkaConsumer('test-topic',
                             # group_id='my-group',
                             bootstrap_servers=['127.0.0.1:9092'])

    # e.g., for unicode: `message.value.decode('utf-8')`
    print(consumer)

    for message in consumer:
        print(message)
        print ("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
                                              message.offset, message.key,
                                              message.value))

if __name__ == '__main__':
    consumer_demo()