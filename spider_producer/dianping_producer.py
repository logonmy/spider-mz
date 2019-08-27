# -*- coding:utf-8 -*-
from bs4 import BeautifulSoup
from utils import spider_utils
from spider_producer.kafka_producer import KafkaProducerUtils

class DianPingProducer(object):
    def __init__(self, page_size, url_start, province,city, region):
        self.page_size = page_size
        self.url_start = url_start
        self.province = province
        self.city = city
        self.region = region


    @staticmethod
    def parse_page_detail_urls(url_org):
        """
        获取点评详情页 urls
        :return: url集合
        """
        response = spider_utils.requests_dianping2(url_org)
        soup = BeautifulSoup(response.text, features="lxml")
    
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


    def build_all_page_urls(self):
        """
        生成需要遍历的urls, 如, 生成从第一页到第50页的urls
        :return: 某个关键字的所有页数
        """
        # url_start = "http://www.dianping.com/hangzhou/ch50/g158r8845"
        url_list = list()
        url_list.append(self.url_start)
    
        for i in range(self.page_size):
            if i > 0:
                # url_former = "http://www.dianping.com/beijing/ch50/g158r5950p" + str(i+1) + "?cpt=5220127%2C19813864"
                url_former = self.url_start + "p" + str(i+1)
                url_list.append(url_former)
    
        return url_list


    def get_all_detail_page_urls(self):
        """
        遍历解析获取到的 url_set
        :return: 详情页url
        """
        str1 = ""
        for url_org in self.build_all_page_urls():
            print(url_org)
            url_sets = self.parse_page_detail_urls(url_org)
    
            for res in url_sets:
                print(res)
                str1 = str1 + self.province + '^' + self.city + '^' + self.region + '^' + res + "\n"
    
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

if __name__ == '__main__':
    page_size1 = 22
    url_start1 = 'http://www.dianping.com/hangzhou/ch50/g158r58'
    province1 = '浙江省'
    city1 = '杭州市'
    region1 = '上城区'

    dian_ping_producer = DianPingProducer(page_size1, url_start1, province1, city1, region1)
    dian_ping_producer.write_page_urls_kafka()