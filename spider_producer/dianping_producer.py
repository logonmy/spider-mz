# -*- coding:utf-8 -*-
from bs4 import BeautifulSoup
from utils import spider_utils2
from spider_producer.kafka_producer import KafkaProducerUtils
from configparser import ConfigParser
import asyncio
from pyppeteer import launch
from cookie_pools import redis_helper


cfg = ConfigParser()
cfg.read('../config/config.ini')


width, height = 1280, 800
class DianPingProducer(object):
    def __init__(self, province, city, ip_proxy_host, ssh_ip):
        self.province = province
        self.city = city
        self.request_dp = spider_utils2.SpiderUtils(ip_proxy_host, ssh_ip)
        self.redis_client = redis_helper.RedisHelper()

    def parse_page_detail_urls(self,url_org):
        """
        获取点评详情页 urls
        :return: url集合
        """
        random_key = self.redis_client.get_random_key()
        cookies_bytes = self.redis_client.get(random_key)

        # 字节转字典
        cookies_str = str(cookies_bytes, encoding='utf-8')
        cookies = eval(cookies_str)

        if '_lxsdk_s' in cookies.keys():
            cookies['_lxsdk_s'] = str(cookies['_lxsdk_s'])[:-1] + str(3)
            # print("cookies-----", cookies)
            # print(cookies['_lxsdk_s'])

        response = self.request_dp.requests_dp(url_org, cookies=cookies)

        response_text = response.text
        if response_text.find('é¡µé¢ä¸å­å¨ | ç¾å¢ç¹è¯') != -1:

            print('4466-- 更换IP重新解析')
            self.redis_client.del_record(random_key)
            print('删除成功')
            self.request_dp.change_ip()
            return self.parse_page_detail_urls(url_org)


        else:
            soup = BeautifulSoup(response_text, features="lxml")
            # 存储获取到的url
            url_set = set([])
            for link in soup.find_all("a"):
                ll =  link.get("href")

                # 获取满足条件的url
                if isinstance(ll, str):
                    if ll.find("http://www.dianping.com/shop") == 0 and ll.find("#")==-1:
                        if ll.find("review") == -1:
                            url_set.add(ll)

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

    def get_all_detail_page_urls(self, url_page_list):
        """
        遍历解析获取到的 url_set
        :return: 详情页url
        """
        str1 = ""
        for line in url_page_list:

            province = line.strip('\n').split('^')[0]
            city = line.strip('\n').split('^')[1]
            region = line.strip('\n').split('^')[2]
            url_org = line.strip('\n').split('^')[3]

            print(url_org)
            url_sets = self.parse_page_detail_urls(url_org)
            for res in url_sets:
                print(res)
                str1 = str1 + province + '^' + city + '^' + region + '^' + res + "\n"
    
        with open("url_all.txt", "a+") as f:
            f.write(str1)


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
        browser = await launch(headless=False, autoClose=False, args=['--disable-infobars', f'--window-size={width},{height}'])

        page = await browser.newPage()

        await page.setViewport({'width': width, 'height': height})
        await page.goto(url1, {'waitUntil':'domcontentloaded'}) # 不加这个参数会, 点评页面会加载很久

        # print(await page.cookies())
        # print(page.url)

        #
        await page.click('#nav > div > ul > li:nth-child(5) > div.primary-container > span > a:nth-child(3)')

        await asyncio.sleep(2)
        pages = await browser.pages()
        await pages[-1].click('#classfy > a:nth-child(2)')

        # 如果不加这行, 不会加载到这个页面的内容
        await pages[-1].waitForNavigation()

        # print(pages[-1].url)
        content = await pages[-1].content()

        soup = BeautifulSoup(content, features="lxml")
        # print(content)

        all_regions = soup.find('div', attrs={'id':'region-nav'}).find_all('a')

        # print(all_regions)

        url_list = list()

        page = await browser.newPage()
        for item in all_regions:
            # await asyncio.sleep(2)
            url = item.get('href')
            region = item.get_text()
            # print(url, region)

            await page.goto(url, {'waitUntil':'domcontentloaded'})
            content1 = await page.content()
            soup1 = BeautifulSoup(content1, features="lxml")
            max_size = soup1.find('div', attrs={'class':'page'}).find_all('a')[-2].get('title')

            # print('最大页码', max_size)

            url_list.append(self.province + '^' + self.city + '^' +  region + '^' + url)

            for i in range(int(max_size)):
                if i > 0:
                    # url_former = "http://www.dianping.com/beijing/ch50/g158r5950p" + str(i+1) + "?cpt=5220127%2C19813864"
                    url_former = url + "p" + str(i+1)
                    url_list.append(self.province + '^' + self.city + '^' +  region + '^' + url_former)

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

    ssh_proxy4 = cfg.get('proxy_host', 'host4')
    print(ssh_proxy4)
    # ss = SpiderUtils('../config/ip_proxy_host4', ip_proxy)

    dp = DianPingProducer('浙江省','杭州市','../config/ip_proxy_host4', ssh_proxy4)
    # url_page_list = asyncio.get_event_loop().run_until_complete(dp.get_all_page_urls('http://www.dianping.com/nanjing'))

    url_page_list = ['浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p2', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p3', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p4', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p5', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p6', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p7', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p8', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p9', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p10', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p11', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p12', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p13', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p14', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p15', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p16', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p17', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p18', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p19', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p20', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p21', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p22', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p23', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p24', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p25', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p26', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p27', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p28', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p29', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p30', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p31', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p32', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p33', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p34', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p35', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p36', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p37', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p38', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p39', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p40', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p41', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p42', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p43', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p44', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p45', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p46', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p47', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p48', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p49', '浙江省^杭州市^秦淮区^http://www.dianping.com/nanjing/ch50/g158r69p50', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p2', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p3', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p4', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p5', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p6', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p7', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p8', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p9', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p10', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p11', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p12', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p13', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p14', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p15', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p16', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p17', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p18', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p19', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p20', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p21', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p22', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p23', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p24', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p25', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p26', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p27', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p28', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p29', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p30', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p31', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p32', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p33', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p34', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p35', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p36', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p37', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p38', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p39', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p40', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p41', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p42', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p43', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p44', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p45', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p46', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p47', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p48', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p49', '浙江省^杭州市^鼓楼区^http://www.dianping.com/nanjing/ch50/g158r65p50', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66p2', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66p3', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66p4', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66p5', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66p6', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66p7', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66p8', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66p9', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66p10', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66p11', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66p12', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66p13', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66p14', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66p15', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66p16', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66p17', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66p18', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66p19', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66p20', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66p21', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66p22', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66p23', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66p24', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66p25', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66p26', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66p27', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66p28', '浙江省^杭州市^玄武区^http://www.dianping.com/nanjing/ch50/g158r66p29', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p2', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p3', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p4', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p5', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p6', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p7', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p8', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p9', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p10', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p11', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p12', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p13', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p14', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p15', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p16', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p17', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p18', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p19', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p20', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p21', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p22', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p23', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p24', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p25', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p26', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p27', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p28', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p29', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p30', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p31', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p32', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p33', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p34', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p35', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p36', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p37', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p38', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p39', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p40', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p41', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p42', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p43', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p44', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p45', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p46', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p47', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p48', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p49', '浙江省^杭州市^建邺区^http://www.dianping.com/nanjing/ch50/g158r67p50', '浙江省^杭州市^雨花台区^http://www.dianping.com/nanjing/ch50/g158r1685', '浙江省^杭州市^雨花台区^http://www.dianping.com/nanjing/ch50/g158r1685p2', '浙江省^杭州市^雨花台区^http://www.dianping.com/nanjing/ch50/g158r1685p3', '浙江省^杭州市^雨花台区^http://www.dianping.com/nanjing/ch50/g158r1685p4', '浙江省^杭州市^雨花台区^http://www.dianping.com/nanjing/ch50/g158r1685p5', '浙江省^杭州市^雨花台区^http://www.dianping.com/nanjing/ch50/g158r1685p6', '浙江省^杭州市^雨花台区^http://www.dianping.com/nanjing/ch50/g158r1685p7', '浙江省^杭州市^雨花台区^http://www.dianping.com/nanjing/ch50/g158r1685p8', '浙江省^杭州市^雨花台区^http://www.dianping.com/nanjing/ch50/g158r1685p9', '浙江省^杭州市^雨花台区^http://www.dianping.com/nanjing/ch50/g158r1685p10', '浙江省^杭州市^雨花台区^http://www.dianping.com/nanjing/ch50/g158r1685p11', '浙江省^杭州市^雨花台区^http://www.dianping.com/nanjing/ch50/g158r1685p12', '浙江省^杭州市^雨花台区^http://www.dianping.com/nanjing/ch50/g158r1685p13', '浙江省^杭州市^雨花台区^http://www.dianping.com/nanjing/ch50/g158r1685p14', '浙江省^杭州市^雨花台区^http://www.dianping.com/nanjing/ch50/g158r1685p15', '浙江省^杭州市^雨花台区^http://www.dianping.com/nanjing/ch50/g158r1685p16', '浙江省^杭州市^雨花台区^http://www.dianping.com/nanjing/ch50/g158r1685p17', '浙江省^杭州市^雨花台区^http://www.dianping.com/nanjing/ch50/g158r1685p18', '浙江省^杭州市^雨花台区^http://www.dianping.com/nanjing/ch50/g158r1685p19', '浙江省^杭州市^雨花台区^http://www.dianping.com/nanjing/ch50/g158r1685p20', '浙江省^杭州市^雨花台区^http://www.dianping.com/nanjing/ch50/g158r1685p21', '浙江省^杭州市^雨花台区^http://www.dianping.com/nanjing/ch50/g158r1685p22', '浙江省^杭州市^雨花台区^http://www.dianping.com/nanjing/ch50/g158r1685p23', '浙江省^杭州市^雨花台区^http://www.dianping.com/nanjing/ch50/g158r1685p24', '浙江省^杭州市^雨花台区^http://www.dianping.com/nanjing/ch50/g158r1685p25', '浙江省^杭州市^雨花台区^http://www.dianping.com/nanjing/ch50/g158r1685p26', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p2', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p3', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p4', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p5', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p6', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p7', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p8', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p9', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p10', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p11', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p12', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p13', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p14', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p15', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p16', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p17', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p18', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p19', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p20', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p21', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p22', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p23', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p24', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p25', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p26', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p27', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p28', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p29', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p30', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p31', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p32', '浙江省^杭州市^栖霞区^http://www.dianping.com/nanjing/ch50/g158r1683p33', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p2', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p3', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p4', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p5', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p6', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p7', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p8', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p9', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p10', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p11', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p12', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p13', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p14', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p15', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p16', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p17', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p18', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p19', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p20', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p21', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p22', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p23', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p24', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p25', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p26', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p27', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p28', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p29', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p30', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p31', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p32', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p33', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p34', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p35', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p36', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p37', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p38', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p39', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p40', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p41', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p42', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p43', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p44', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p45', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p46', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p47', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p48', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p49', '浙江省^杭州市^江宁区^http://www.dianping.com/nanjing/ch50/g158r619p50', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p2', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p3', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p4', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p5', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p6', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p7', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p8', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p9', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p10', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p11', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p12', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p13', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p14', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p15', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p16', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p17', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p18', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p19', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p20', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p21', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p22', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p23', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p24', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p25', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p26', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p27', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p28', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p29', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p30', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p31', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p32', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p33', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p34', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p35', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p36', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p37', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p38', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p39', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p40', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p41', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p42', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p43', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p44', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p45', '浙江省^杭州市^浦口区^http://www.dianping.com/nanjing/ch50/g158r1958p46', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p2', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p3', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p4', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p5', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p6', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p7', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p8', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p9', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p10', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p11', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p12', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p13', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p14', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p15', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p16', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p17', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p18', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p19', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p20', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p21', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p22', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p23', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p24', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p25', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p26', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p27', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p28', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p29', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p30', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p31', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p32', '浙江省^杭州市^六合区^http://www.dianping.com/nanjing/ch50/g158r1686p33', '浙江省^杭州市^溧水区^http://www.dianping.com/nanjing/ch50/g158c415', '浙江省^杭州市^溧水区^http://www.dianping.com/nanjing/ch50/g158c415p2', '浙江省^杭州市^溧水区^http://www.dianping.com/nanjing/ch50/g158c415p3', '浙江省^杭州市^溧水区^http://www.dianping.com/nanjing/ch50/g158c415p4', '浙江省^杭州市^溧水区^http://www.dianping.com/nanjing/ch50/g158c415p5', '浙江省^杭州市^溧水区^http://www.dianping.com/nanjing/ch50/g158c415p6', '浙江省^杭州市^溧水区^http://www.dianping.com/nanjing/ch50/g158c415p7', '浙江省^杭州市^溧水区^http://www.dianping.com/nanjing/ch50/g158c415p8', '浙江省^杭州市^溧水区^http://www.dianping.com/nanjing/ch50/g158c415p9', '浙江省^杭州市^溧水区^http://www.dianping.com/nanjing/ch50/g158c415p10', '浙江省^杭州市^溧水区^http://www.dianping.com/nanjing/ch50/g158c415p11', '浙江省^杭州市^溧水区^http://www.dianping.com/nanjing/ch50/g158c415p12', '浙江省^杭州市^溧水区^http://www.dianping.com/nanjing/ch50/g158c415p13', '浙江省^杭州市^溧水区^http://www.dianping.com/nanjing/ch50/g158c415p14', '浙江省^杭州市^溧水区^http://www.dianping.com/nanjing/ch50/g158c415p15', '浙江省^杭州市^高淳区^http://www.dianping.com/nanjing/ch50/g158c827', '浙江省^杭州市^高淳区^http://www.dianping.com/nanjing/ch50/g158c827p2', '浙江省^杭州市^高淳区^http://www.dianping.com/nanjing/ch50/g158c827p3', '浙江省^杭州市^高淳区^http://www.dianping.com/nanjing/ch50/g158c827p4', '浙江省^杭州市^高淳区^http://www.dianping.com/nanjing/ch50/g158c827p5', '浙江省^杭州市^高淳区^http://www.dianping.com/nanjing/ch50/g158c827p6', '浙江省^杭州市^高淳区^http://www.dianping.com/nanjing/ch50/g158c827p7', '浙江省^杭州市^高淳区^http://www.dianping.com/nanjing/ch50/g158c827p8']

    dp.get_all_detail_page_urls(url_page_list)
