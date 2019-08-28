# -*- coding:utf-8 -*-
from kafka import KafkaProducer
import json
from configparser import ConfigParser
from ast import literal_eval

cfg = ConfigParser()
cfg.read('../config/config.ini')

class KafkaProducerUtils(object):
    def __init__(self, server, topic):
        self.server = server
        self.topic = topic
        # kafka-broker 地址
        self.producer2 = KafkaProducer(bootstrap_servers=server,
                                       value_serializer=lambda m: json.dumps(m).encode('utf-8'))

    def producer(self, message):
        self.producer2.send(self.topic, message)


    def close(self):
        self.producer2.close()

if __name__ == '__main__':
    server2_list = literal_eval(cfg.get('kafka','bootstrap_servers')) # 将 字符串类型的list 转成 list
    topic2 = cfg.get('kafka','topic')

    producer1 = KafkaProducerUtils(server2_list, topic2)

    # res_dict = dict()
    # res_dict['province'] = '浙江省'
    # res_dict['city'] = '杭州市'
    # res_dict['region'] = '西湖区'
    # res_dict['url'] = 'http://www.dianping.com/shop/18427712'
    #
    # for i in range(1):
    #     res_dict['url'] = 'http://www.dianping.com/shop/91895926'
    #     producer1.producer(res_dict)
    #
    # producer1.close()

    with open('../spider_producer/url_all.txt') as f:
        for line in f.readlines():
            res_dict = dict()

            line_list = line.strip('\n').split('^')

            res_dict['province'] = line_list[0]
            res_dict['city'] = line_list[1]
            res_dict['region'] = line_list[2]
            res_dict['url'] = line_list[3]

            # print(res_dict)

            producer1.producer(res_dict)


    producer1.close()