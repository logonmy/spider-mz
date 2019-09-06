# -*- coding:utf-8 -*-
from kafka import KafkaConsumer
from configparser import ConfigParser
from ast import literal_eval
import multiprocessing
import time
from spider_consumer.dianping_consumer import DianPingConsumer
from utils.spider_utils2 import SpiderUtils
from pyppeteer import launch
import asyncio
from bs4 import BeautifulSoup
import re


cfg = ConfigParser()
cfg.read('../config/config.ini')

"""多进程的方式"""
class KafkaConsumerUtils(multiprocessing.Process):
    def __init__(self, server, topic, group_id, process_id, requests_dp:SpiderUtils):
        """
        :param server:
        :param topic:
        :param group_id:
        :param process_id:
        :param requests_dp:
        """
        super(KafkaConsumerUtils, self).__init__()
        self.server = server
        self.topic = topic
        self.group_id = group_id
        self.process_id = process_id
        self.requests_dp = requests_dp # ssh代理

        self.parse_utils = DianPingConsumer(cfg.get('file_path','write_file_path1'), requests_dp, '')


    def run(self):
        consumer = KafkaConsumer(self.topic,
                                 group_id=self.group_id,
                                 bootstrap_servers=self.server)

        # message.value.decode('utf-8')
        for message in consumer:

            # 字节转字典
            message_str = str(message.value, encoding='utf-8')
            message_dict = eval(message_str)

            res = self.parse_utils.kafka_to_file(message_dict)
            print(res)

if __name__ == '__main__':
    pass
