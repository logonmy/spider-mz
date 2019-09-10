# -*- coding:utf-8 -*-
from bs4 import BeautifulSoup
from utils import spider_utils2
from spider_producer.kafka_producer import KafkaProducerUtils
from configparser import ConfigParser
import asyncio
from pyppeteer import launch
from cookie_pools import redis_helper
import time
import random

cfg = ConfigParser()
cfg.read('../config/config.ini')


width, height = 1280, 800
class DianPingProducer(object):
    def __init__(self, province, city, ip_proxy_host, ssh_ip):
        self.province = province
        self.city = city
        self.dianping = spider_utils2.SpiderUtils(ip_proxy_host, ssh_ip)
        self.redis_client = redis_helper.RedisHelper()


    def parse_page_detail_urls(self, url_org):
        """
        获取点评详情页 urls
        :return: url集合
        """
        random_key = self.redis_client.get_random_key()
        cookies_bytes = self.redis_client.get(random_key)

        # 字节转字典
        cookies_str = str(cookies_bytes, encoding='utf-8')
        cookies = eval(cookies_str)


        add_list = [20,40,60,80,100,120,121,140,160,180,181,200,221]
        if '_lxsdk_s' in cookies.keys():
            # cookies['_lxsdk_s'] = str(cookies['_lxsdk_s'])[:-1] + str(21)
            # print("cookies-----", cookies)

            ss1 = cookies.get('_lxsdk_s')
            cookies['_lxsdk_s'] = ss1[0: ss1.rindex('C')+1] + str(random.choice(add_list))

        response = self.dianping.requests_dp(url_org, cookies=cookies)

        if isinstance(response, str):
            soup = BeautifulSoup(response, features="lxml")
            # 存储获取到的url
            url_set = set([])
            for link in soup.find_all("a"):
                ll =  link.get("href")

                # 获取满足条件的url
                if isinstance(ll, str):
                    if ll.find("http://www.dianping.com/shop") == 0 and ll.find("#")== -1:
                        if ll.find("review") == -1:
                            url_set.add(ll)

            if len(url_set) == 0:
                print('删除cookie, 重新解析')
                time.sleep(2)
                self.redis_client.del_record(random_key)
                return self.parse_page_detail_urls(url_org)

            return url_set

        else:
            response_text = response.text
            if response_text.find('é¡µé¢ä¸å­å¨ | ç¾å¢ç¹è¯') != -1:
                print('4466-- 更换IP重新解析')
                self.redis_client.del_record(random_key)
                self.dianping.change_ip()
                return self.parse_page_detail_urls(url_org)

            else:
                soup = BeautifulSoup(response_text, features="lxml")
                # 存储获取到的url
                url_set = set([])
                for link in soup.find_all("a"):
                    ll =  link.get("href")

                    # 获取满足条件的url
                    if isinstance(ll, str):
                        if ll.find("http://www.dianping.com/shop") == 0 and ll.find("#")== -1:
                            if ll.find("review") == -1:
                                url_set.add(ll)

                if len(url_set) == 0:
                    print('删除cookie, 重新解析')
                    time.sleep(2)
                    self.redis_client.del_record(random_key)
                    return self.parse_page_detail_urls(url_org)

                return url_set

    # def build_all_page_urls(self):
    #     """
    #     生成需要遍历的urls, 如, 生成从第一页到第50页的urls
    #     :return: 某个关键字的所有页数
    #     """
    #     # url_start = "http://www.dianping.com/hangzhou/ch50/g158r8845"
    #     url_list = list()
    #     url_list.append(self.url_start)
    #
    #     for i in range(self.page_size):
    #         if i > 0:
    #             # url_former = "http://www.dianping.com/beijing/ch50/g158r5950p" + str(i+1) + "?cpt=5220127%2C19813864"
    #             url_former = self.url_start + "p" + str(i+1)
    #             url_list.append(url_former)
    #
    #     return url_list

    def get_all_detail_page_urls(self, url_page_list1):
        """
        遍历解析获取到的 url_set
        :return: 详情页url
        """

        for line1 in url_page_list1:
            str1 = ''

            province = line1.strip('\n').split('^')[0]
            city = line1.strip('\n').split('^')[1]
            region = line1.strip('\n').split('^')[2]
            url_org = line1.strip('\n').split('^')[3]

            url_sets = self.parse_page_detail_urls(url_org)
            for res in url_sets:
                print(res)
                str1 = str1 + province + '^' + city + '^' + region + '^' + res + "\n"


            with open("url_all.txt", "a+") as f1:
                f1.write(str1)


    def write_page_urls_kafka(self):
        """
        遍历解析获取到的 url_set,
        写入kafka
        :return: 详情页url
        """
        producer1 = KafkaProducerUtils('', '')
        for url_org in self.build_all_page_urls():
            print(url_org)
            url_sets = self.parse_page_detail_urls(url_org)

            for res in url_sets:
                # 拼接成json发送
                res_dict = dict()
                res_dict['province'] = self.province
                res_dict['city'] = self.city
                res_dict['region'] = self.region
                res_dict['url'] = res

                print(res_dict)
                producer1.producer(res_dict)

        producer1.close()

    def urls_from_file_to_kafka(self):
        """
        遍历解析获取到的 url_set,
        写入kafka
        :return: 详情页url
        """
        producer1 = KafkaProducerUtils('', '')
        for url_org in self.build_all_page_urls():
            print(url_org)
            url_sets = self.parse_page_detail_urls(url_org)

            for res in url_sets:
                # 拼接成json发送
                res_dict = dict()
                res_dict['province'] = self.province
                res_dict['city'] = self.city
                res_dict['region'] = self.region
                res_dict['url'] = res

                print(res_dict)
                producer1.producer(res_dict)

        producer1.close()

    async def get_all_page_urls(self, url1):
        # --disable-infobars, 禁止提示
        # window-size, 设置页面显示
        browser = await launch(headless=False, autoClose=False, args=['--disable-infobars',
                                                                      f'--window-size={width},{height}'])
        page = await browser.newPage()
        await page.setViewport({'width': width, 'height': height})
        await page.goto(url1, {'waitUntil':'domcontentloaded'}) # 不加这个参数会, 点评页面会加载很久
        await page.click('#nav > div > ul > li:nth-child(5) > div.primary-container > span > a:nth-child(3)')

        await asyncio.sleep(1)
        pages = await browser.pages()
        await pages[-1].click('#classfy > a:nth-child(2)')

        # 如果不加这行, 不会加载到这个页面的内容
        await pages[-1].waitForNavigation()

        # print(pages[-1].url)
        content = await pages[-1].content()

        soup = BeautifulSoup(content, features="lxml")
        # print(content)

        # 获取该城市的所有区域
        all_regions = soup.find('div', attrs={'id':'region-nav'}).find_all('a')

        # print(all_regions)

        url_list = list()

        page = await browser.newPage()

        for item in all_regions:

            print(item)
            page_all = ''
            if 'http' or 'https' in str(item):
                print(item)

                # await asyncio.sleep(1)
                url = item.get('href')
                region = item.get_text()
                # print(url, region)

                await page.goto(url, {'waitUntil':'domcontentloaded'})
                content1 = await page.content()
                soup1 = BeautifulSoup(content1, features="lxml")

                try:
                    max_size = soup1.find('div', attrs={'class':'page'}).find_all('a')[-2].get('title')
                except Exception as e:
                    max_size = 0
                    print(e)

                # print('最大页码', max_size)

                first_page = self.province + '^' + self.city + '^' +  region + '^' + url
                page_all = page_all + first_page + '\n'

                url_list.append(first_page)

                if max_size != 0:
                    for i in range(int(max_size)):
                        if i > 0:
                            # url_former = "http://www.dianping.com/beijing/ch50/g158r5950p" + str(i+1) + "?cpt=5220127%2C19813864"
                            url_former = url + "p" + str(i+1)
                            page_num_str = self.province + '^' + self.city + '^' +  region + '^' + url_former

                            page_all = page_all + page_num_str + '\n'
                            url_list.append(page_num_str)

            with open('url_page.txt', 'a+') as f:
                f.write(page_all)

            # page.close()
            # browser.close()

        return url_list


if __name__ == '__main__':
    # page_size1 = 9
    # url_start1 = 'http://www.dianping.com/chengdu/ch50/g158c1612'
    # province1 = '四川省'
    # city1 = '成都市'
    # region1 = '蒲江县'
    #
    # ssh_proxy1 = cfg.get('proxy_host', 'host5')
    #
    # dian_ping_producer = DianPingProducer(page_size1, url_start1, province1, city1, region1,
    #                                       '../config/ip_proxy_host5', ssh_proxy1)
    # dian_ping_producer.write_page_urls_kafka()

    ssh_proxy5 = cfg.get('proxy_host', 'host5')
    print(ssh_proxy5)
    # ss = SpiderUtils('../config/ip_proxy_host4', ip_proxy)

    dp = DianPingProducer('湖南省','长沙市','../config/ip_proxy_host5', ssh_proxy5)

    # asyncio.get_event_loop().run_until_complete(dp.get_all_page_urls('http://www.dianping.com/changsha'))

    # lll = ['江苏省^南京市^李遂去^http://www.dianping.com/nanjing/ch50/g158r69p30']
    # lll = ['江苏省^南京市^秦淮区^http://www.baidu.com']

    url_page_list = list()
    with open('url_page.txt') as f:
        for line in f.readlines():
            url_page_list.append(line.strip('\n'))

    dp.get_all_detail_page_urls(url_page_list)
