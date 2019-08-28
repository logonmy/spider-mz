# -*- coding:utf-8 -*-
from kafka import KafkaConsumer
from configparser import ConfigParser
from ast import literal_eval

cfg = ConfigParser()
cfg.read('../config/config.ini')

"""此种方式可以启动多个脚本实现并行执行"""
class KafkaConsumerUtils(object):
    def __init__(self, server, topic, group_id):
        self.server = server
        self.topic = topic
        self.group_id = group_id


    def consumer(self):
        # consumer = KafkaConsumer('test-topic',
        #                          # group_id='my-group',
        #                          bootstrap_servers=['127.0.0.1:9092'])

        consumer = KafkaConsumer(self.topic,
                                 group_id=self.group_id,
                                 bootstrap_servers=self.server)

        # `message.value.decode('utf-8')`
        for message in consumer:
            # print(message)
            # print(type(message.value))
            # print ('--23--', message.value.decode('utf-8'))

            # 字节转字典
            message_str = str(message.value, encoding='utf-8')
            message_dict = eval(message_str)
            print(message_dict['province'])
            print(message_dict['city'])
            print(message_dict['region'])
            print(message_dict['url'])

if __name__ == '__main__':
    server2_list = literal_eval(cfg.get('kafka','bootstrap_servers')) # 将 字符串类型的list 转成 list
    topic2 = cfg.get('kafka','topic')
    group2 = cfg.get('kafka','group_id')

    consumer1 = KafkaConsumerUtils(server2_list, topic2, group2)
    consumer1.consumer()

