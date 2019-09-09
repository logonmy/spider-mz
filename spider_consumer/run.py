# -*- coding:utf-8 -*-
from kafka import KafkaConsumer
from configparser import ConfigParser
from ast import literal_eval
import multiprocessing
import time
from spider_consumer.dianping_consumer import DianPingConsumer
from utils.spider_utils2 import SpiderUtils
from spider_consumer.kafka_consumer2 import KafkaConsumerUtils

cfg = ConfigParser()
cfg.read('../config/config.ini')


server2_list = literal_eval(cfg.get('kafka','bootstrap_servers')) # 将 字符串类型的list 转成 list
topic2 = cfg.get('kafka','topic')
group2 = cfg.get('kafka','group_id')

def run_py_requests():
    # ##### 启动 consumer1
    # ssh_proxy1 = cfg.get('proxy_host', 'host1')
    # print('线程1启动-------')
    # spider_utils1 = SpiderUtils('../config/ip_proxy_host1', ssh_proxy1)
    # consumer1 = KafkaConsumerUtils(server2_list, topic2, group2, '进程1', spider_utils1)
    # consumer1.start()
    # #
    # ##### 启动 consumer2
    # ssh_proxy2 = cfg.get('proxy_host', 'host2')
    # print('线程2启动-------')
    # spider_utils2 = SpiderUtils('../config/ip_proxy_host2', ssh_proxy2)
    # consumer2 = KafkaConsumerUtils(server2_list, topic2, group2, '进程2', spider_utils2)
    # consumer2.start()
    # # #
    # # #
    # # ##### 启动 consumer3
    # ssh_proxy3 = cfg.get('proxy_host', 'host3')
    # print('线程3启动-------')
    # spider_utils3 = SpiderUtils('../config/ip_proxy_host3', ssh_proxy3)
    # consumer3 = KafkaConsumerUtils(server2_list, topic2, group2, '进程3', spider_utils3)
    # consumer3.start()


    #### 启动 consumer4
    ssh_proxy4 = cfg.get('proxy_host', 'host4')
    print('线程4启动-------')
    spider_utils4 = SpiderUtils('../config/ip_proxy_host4', ssh_proxy4)
    consumer4 = KafkaConsumerUtils(server2_list, topic2, group2, '进程4', spider_utils4)
    consumer4.start()

    ### 启动 consumer5
    ssh_proxy5 = cfg.get('proxy_host', 'host5')
    print('线程5启动-------')
    spider_utils5 = SpiderUtils('../config/ip_proxy_host5', ssh_proxy5)
    consumer5 = KafkaConsumerUtils(server2_list, topic2, group2, '进程5', spider_utils5)
    consumer5.start()


def run_pyppeteer():
    ##### 启动 consumer4
    ssh_proxy4 = cfg.get('proxy_host', 'host4')

    print(ssh_proxy4)
    print('线程4启动-------')


    spider_utils4 = SpiderUtils('../config/ip_proxy_host4', ssh_proxy4)
    consumer4 = KafkaConsumerUtils(server2_list, topic2, group2, '进程4', spider_utils4)
    consumer4.start()


if __name__ == '__main__':
    run_py_requests()