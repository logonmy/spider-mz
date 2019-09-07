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
width, height = 1280, 800

"""多进程的方式"""
class KafkaConsumerUtils(object):
    def __init__(self, server, topic, group_id, process_id, requests_dp:SpiderUtils):
        """
        :param server:
        :param topic:
        :param group_id:
        :param process_id:
        :param requests_dp:
        """
        print('初始化KafkaConsumerUtils-------')
        self.server = server
        self.topic = topic
        self.group_id = group_id
        self.process_id = process_id
        self.requests_dp = requests_dp # ssh代理


    async def run(self):
        consumer = KafkaConsumer(self.topic,
                                 group_id=self.group_id,
                                 bootstrap_servers=self.server)

        browser = await launch(headless=False, autoClose=False, args=['--disable-infobars',
                                                                      f'--window-size={width},{height}',
                                                                      '--proxy-server=117.83.137.7:32982',
                                                                      '--proxy-server=117.83.137.7:32982'])

        page = await browser.newPage()
        await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36')

        await page.setViewport({'width': width, 'height': height})

        for message in consumer:
            # 字节转字典
            message_str = str(message.value, encoding='utf-8')
            message_dict = eval(message_str)

            url2 = message_dict['url']
            await self.parse_dp_url(page, url2)


    async def parse_dp_url(self, page, dp_url):

        try:
            await page.goto(dp_url, {'waitUntil':'domcontentloaded','timeout': 1000*30 })
            content = await page.content()
            title = await page.title()
            if title == '验证中心':
                print('需要验证---------')
                await asyncio.sleep(5)
                print(await page.content())
                await page.hover('#yodaMoveingBar')
                await page.mouse.down()
                await page.mouse.move(900, 0, {'steps': 7})
                await page.mouse.up()
            else:
                await self.parse_url_utils(content, dp_url)
        except Exception as e:
            print(e)






    # @staticmethod
    async def parse_url_utils(self, html_content, dp_url):
        soup = BeautifulSoup(html_content, features="lxml")
        # 如果counter_none 值为4,则说明IP被封,需更换IP
        counter_none = 0

        # 医院名
        hospital_name = ""
        try:
            hospital_name, b = soup.find("h1").stripped_strings
            # print(hospital_name)
        except Exception as e:
            counter_none += 1
            print(e)

        # 地址
        address = ""
        try:
            for i in soup.find("div", attrs={"class":"expand-info address"}).find_all("span"):
                address += (str(i.get_text()).strip())
                # print(address)
        except Exception as e:
            counter_none += 1
            print(e)

        # 电话
        tel = ""
        try:
            tel = str(soup.find("p", attrs={"class":"expand-info tel"}).find("span", "item").get_text()).strip()
            # print(tel)
        except Exception as e:
            counter_none += 1
            print(e)

        # 星级
        score = ""
        try:
            stars_str = soup.find("div", attrs={"class":"brief-info"}).find_all("span")[0]
            score = re.findall(r"\d+\.?\d*",str(stars_str).strip())[0]
        except Exception as e:
            counter_none += 1
            print(e)

        # 检测IP是否被封
        if counter_none == 4:
            print("失效了")
        else:
            str2 = dp_url + "^" + hospital_name + "^" + address + "^" + tel + "^" + score
            print(multiprocessing.current_process().name)
            print(str2)
            # return str2


def run1():
    server2_list = literal_eval(cfg.get('kafka','bootstrap_servers')) # 将 字符串类型的list 转成 list
    topic2 = cfg.get('kafka','topic')
    group2 = cfg.get('kafka','group_id')


    ##### 启动 consumer4
    ssh_proxy4 = cfg.get('proxy_host', 'host4')
    print('线程4启动-------')
    spider_utils4 = SpiderUtils('../config/ip_proxy_host4', ssh_proxy4)

    consumer4 = KafkaConsumerUtils(server2_list, topic2, group2, '进程4', spider_utils4)
    asyncio.get_event_loop().run_until_complete(consumer4.run())


if __name__ == '__main__':

    # asyncio.get_event_loop().run_until_complete(consumer4.run())

    # pool = multiprocessing.Pool(processes=4) # 创建4个进程

    # # pool.apply_async(asyncio.get_event_loop().run_until_complete(consumer4.run()))
    # pool.apply_async(asyncio.get_event_loop().run_until_complete(consumer4.run()))
    # pool.close() # 关闭进程池，表示不能在往进程池中添加进程
    # pool.join()

    p1 = multiprocessing.Process(target=run1)
    p2 = multiprocessing.Process(target=run1)

    p1.start()
    # p2.start()
