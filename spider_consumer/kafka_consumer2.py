# -*- coding:utf-8 -*-
from kafka import KafkaConsumer
from configparser import ConfigParser
from ast import literal_eval
import multiprocessing
import time
from spider_consumer.dianping_consumer import DianPingConsumer

cfg = ConfigParser()
cfg.read('../config/config.ini')


"""多进程的方式"""
class KafkaConsumerUtils(multiprocessing.Process):
    def __init__(self, server, topic, group_id, process_id, ssh_proxy):
        super(KafkaConsumerUtils, self).__init__()
        self.server = server
        self.topic = topic
        self.group_id = group_id
        self.process_id = process_id
        self.ssh_proxy = ssh_proxy # ssh代理

        self.parse_utils = DianPingConsumer(cfg.get('file_path','write_file_path1'))



    def run(self):
        consumer = KafkaConsumer(topics=self.topic,
                                 group_id=self.group_id,
                                 bootstrap_servers=self.server)

        # message.value.decode('utf-8')
        for message in consumer:
            # 字节转字典
            message_str = str(message.value, encoding='utf-8')
            message_dict = eval(message_str)
            print(message_dict['province'], self.process_id)
            print(message_dict['city'])
            print(message_dict['region'])

            url2 = message_dict['url']
            print(url2)

            res = self.parse_utils.kafka_to_file(message_dict)

            print(res)


if __name__ == '__main__':
    server2_list = literal_eval(cfg.get('kafka','bootstrap_servers')) # 将 字符串类型的list 转成 list
    topic2 = cfg.get('kafka','topic')
    group2 = cfg.get('kafka','group_id')

    consumer1 = KafkaConsumerUtils(server2_list, topic2, group2, '进程1')
    consumer1.start()


    consumer2 = KafkaConsumerUtils(server2_list, topic2, group2, '进程2')
    consumer2.start()

