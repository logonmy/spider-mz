# -*- coding:utf-8 -*-
from kafka import KafkaConsumer
from configparser import ConfigParser
from ast import literal_eval
import multiprocessing
import time
from spider_consumer.dianping_consumer import DianPingConsumer
from utils.spider_utils2 import SpiderUtils


cfg = ConfigParser()
cfg.read('../config/config.ini')


"""多进程的方式"""
class KafkaConsumerUtils(multiprocessing.Process):
    def __init__(self, server, topic, group_id, process_id, requests_dp:SpiderUtils):
        print('初始化KafkaConsumerUtils-------')
        super(KafkaConsumerUtils, self).__init__()
        self.server = server
        self.topic = topic
        self.group_id = group_id
        self.process_id = process_id
        self.requests_dp = requests_dp # ssh代理

        self.parse_utils = DianPingConsumer(cfg.get('file_path','write_file_path1'), requests_dp, '')



    def run(self):
        print('run------')
        consumer = KafkaConsumer(self.topic,
                                 group_id=self.group_id,
                                 bootstrap_servers=self.server)

        # message.value.decode('utf-8')

        print(self.topic, self.group_id, self.server)
        print(consumer)
        for message in consumer:

            print('--------------')
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

    ##### 启动 consumer1
    ssh_proxy1 = cfg.get('proxy_host', 'host1')
    print('线程1启动-------')
    spider_utils1 = SpiderUtils('../config/ip_proxy_host1', ssh_proxy1)
    consumer1 = KafkaConsumerUtils(server2_list, topic2, group2, '进程1', spider_utils1)
    consumer1.start()

    ##### 启动 consumer2
    ssh_proxy2 = cfg.get('proxy_host', 'host2')
    print('线程2启动-------')
    spider_utils2 = SpiderUtils('../config/ip_proxy_host2', ssh_proxy2)
    consumer2 = KafkaConsumerUtils(server2_list, topic2, group2, '进程2', spider_utils2)
    consumer2.start()
    #
    #
    # ##### 启动 consumer3
    ssh_proxy3 = cfg.get('proxy_host', 'host3')
    print('线程3启动-------')
    spider_utils3 = SpiderUtils('../config/ip_proxy_host3', ssh_proxy3)
    consumer3 = KafkaConsumerUtils(server2_list, topic2, group2, '进程3', spider_utils3)
    consumer3.start()


    ##### 启动 consumer4
    ssh_proxy4 = cfg.get('proxy_host', 'host4')
    print('线程4启动-------')
    spider_utils4 = SpiderUtils('../config/ip_proxy_host4', ssh_proxy4)
    consumer4 = KafkaConsumerUtils(server2_list, topic2, group2, '进程4', spider_utils4)
    consumer4.start()

    # ##### 启动 consumer5
    # ssh_proxy5 = cfg.get('proxy_host', 'host5')
    # print('线程5启动-------')
    # spider_utils5 = SpiderUtils('../config/ip_proxy_host5', ssh_proxy5)
    # consumer5 = KafkaConsumerUtils(server2_list, topic2, group2, '进程5', spider_utils5)
    # consumer5.start()
