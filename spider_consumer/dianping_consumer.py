# -*- coding:utf-8 -*-
from bs4 import BeautifulSoup
from utils import spider_utils
import re
import os
from utils.spider_utils2 import SpiderUtils
from configparser import ConfigParser
from cookie_pools import redis_helper
import random

cfg = ConfigParser()
cfg.read('../config/config.ini')

class DianPingConsumer(object):
    def __init__(self, write_file_path, requests_dp:SpiderUtils, read_file_path=None):
        self.write_file_path = write_file_path
        self.requests_dp = requests_dp
        self.read_file_path = read_file_path
        self.redis_client = redis_helper.RedisHelper()

    # @staticmethod
    def parse_url_utils(self, url2):
        """
        解析点评详细页 url
        :return:
        """
        ##### 从redis获取cookie
        random_key = self.redis_client.get_random_key()
        cookies_bytes = self.redis_client.get(random_key)

        # 字节转字典
        cookies_str = str(cookies_bytes, encoding='utf-8')
        cookies = eval(cookies_str)
        ##### 从redis获取cookie

        # add_list = [20,40,60,80,100,120,121,140,160,180,181,200,221]
        add_list = [21,41,61,81,121,141]
        if '_lxsdk_s' in cookies.keys():
            # cookies['_lxsdk_s'] = str(cookies['_lxsdk_s'])[:-1] + str(21)
            # print("cookies-----", cookies)

            ss1 = cookies.get('_lxsdk_s')
            cookies['_lxsdk_s'] = ss1[0: ss1.rindex('C')+1] + str(random.choice(add_list))

        response = self.requests_dp.requests_dp(url2, cookies)

        if isinstance(response, str):
            response_text = response
        else:
            response_text = response.text

        # print(response.text)
        # 不能这样使用地址不对,因为本中可能存在这种值
        # if response is not None and response.text.find("request uri not exist") == -1:

        if response_text.find("request uri not exist") != -1:
            return 'URL无效'
        elif response_text.find('é¡µé¢ä¸å­å¨ | ç¾å¢ç¹è¯') != -1:

            print('4477-- 更换IP重新解析')
            self.redis_client.del_record(random_key)
            # print('删除成功')
            self.requests_dp.change_ip()
            return self.parse_url_utils(url2)

        elif response is not None:

            if response_text.find('<h1 class="shop-name">') != -1:
                soup = BeautifulSoup(response_text, features="lxml")

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
                    # print("IP-Cookie失效, 更换....")
                    print("IP-Cookie失效, 更换IP删除该cookie....")

                    self.redis_client.del_record(random_key)
                    print('删除成功')
                    # selenium
                    # cookies = selenium_utils.no_delay_cookies(url)
                    # print(cookies)

                    # self.requests_dp.change_ip_cookies(url2)
                    self.requests_dp.change_ip()
                    print("重新执行该方法")
                    return self.parse_url_utils(url2)
                else:
                    str2 = url2 + "^" + hospital_name + "^" + address + "^" + tel + "^" + score
                    print(hospital_name, address, tel, score)

                    return str2
                    # with open("dianping_data_huangpu_spa.txt", "a+") as f:
                    #     f.write(str2 + "\n")
            else:
                print('#'*20, 'URL解析失败')
                return url2 + '^URL解析失败'
    
    
    def file_to_file(self):
        """
        读取 url_all.txt, 解析后写入文件
        :return: 
        """
        with open(self.read_file_path) as f:
            counter = 1
            flag = False
            last_one_url = ""
            if os.path.exists(self.write_file_path):
                with open(self.write_file_path) as f2:
                    last_one_url = f2.readlines()[-1].split('^')[3]
            else:
                flag = True
        
            for line in f.readlines():
                province = line.strip().split('^')[0]
                city = line.strip().split('^')[1]
                region = line.strip().split('^')[2]
                url = line.strip().split('^')[3]
        
                if last_one_url == url:
                    flag = True
                    continue
        
                if flag is True:
                    print("开始解析第%d行, %s"%(counter, url))
                    str2 = province + '^' + city + '^' + region + '^' + self.parse_url_utils(url)
        
                    with open(self.write_file_path, "a+") as f2:
                        f2.write(str2 + "\n")
                    # print(url)
                    # if counter%150 == 0:
                    #     print("切换")
                    #     spider_utils.change_ip()
                    print("结束解析----------" + '\n')
        
                    counter +=1


    def kafka_to_file(self, message_dict):
        province = message_dict.get('province')
        city = message_dict.get('city')
        region = message_dict.get('region')
        url = message_dict.get('url')

        results = province + '^' + city + '^' + region + '^' + self.parse_url_utils(url)

        with open(self.write_file_path, "a+") as f2:
            f2.write(results + "\n")


if __name__ == '__main__':
    write_file_path1 = 'dianping_hangzhou_data_spa.txt'
    read_file_path1 = '../spider_producer/url_all.txt'


    ip_proxy = cfg.get('proxy_host', 'host1')
    print(ip_proxy)
    ss = SpiderUtils('../config/ip_proxy_host1', ip_proxy)

    dian_ping_consumer = DianPingConsumer(write_file_path1, ss, read_file_path1)

    # dian_ping_consumer.file_to_file()


    res = dian_ping_consumer.parse_url_utils('http://www.dianping.com/shop/568037503')

    print(res)

