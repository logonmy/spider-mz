# # -*- coding:utf-8 -*-
# from bs4 import BeautifulSoup
# from utils import spider_utils
# import re
# import os
#
#
# class DianPingConsumer(object):
#     def __init__(self, write_file_path, read_file_path=None):
#         self.write_file_path = write_file_path
#         self.read_file_path = read_file_path
#
#
#     # @staticmethod
#     def parse_url_utils(self, url2):
#         """
#         解析点评详细页 url
#         :return:
#         """
#         response = spider_utils.requests_dianping2(url2)
#
#         # print(response.text)
#         # 不能这样使用地址不对,因为本中可能存在这种值
#         # if response is not None and response.text.find("地址不对") == -1:
#         if response is not None:
#             soup = BeautifulSoup(response.text, features="lxml")
#             # print(response.text)
#
#             # 如果counter_none 值为4,则说明IP被封,需更换IP
#             counter_none = 0
#
#             # 医院名
#             hospital_name = ""
#             try:
#                 hospital_name, b = soup.find("h1").stripped_strings
#                 # print(hospital_name)
#             except Exception as e:
#                 counter_none += 1
#                 print(e)
#
#             # 地址
#             address = ""
#             try:
#                 for i in soup.find("div", attrs={"class":"expand-info address"}).find_all("span"):
#                     address += (str(i.get_text()).strip())
#                     # print(address)
#             except Exception as e:
#                 counter_none += 1
#                 print(e)
#
#             # 电话
#             tel = ""
#             try:
#                 tel = str(soup.find("p", attrs={"class":"expand-info tel"}).find("span", "item").get_text()).strip()
#                 # print(tel)
#             except Exception as e:
#                 counter_none += 1
#                 print(e)
#
#             # 星级
#             score = ""
#             try:
#                 stars_str = soup.find("div", attrs={"class":"brief-info"}).find_all("span")[0]
#                 score = re.findall(r"\d+\.?\d*",str(stars_str).strip())[0]
#             except Exception as e:
#                 counter_none += 1
#                 print(e)
#
#             # 检测IP是否被封
#             if counter_none == 4:
#                 print("IP-Cookie失效, 更换....")
#                 # selenium
#                 # cookies = selenium_utils.no_delay_cookies(url)
#                 # print(cookies)
#
#                 # spider_utils.change_ip_cookies(url2)
#                 spider_utils.change_ip()
#                 print("重新执行该方法")
#                 return self.parse_url_utils(url2)
#             else:
#                 print('---217----')
#                 str2 = url2 + "^" + hospital_name + "^" + address + "^" + tel + "^" + score
#                 print(hospital_name, address, tel, score)
#
#                 return str2
#                 # with open("dianping_data_huangpu_spa.txt", "a+") as f:
#                 #     f.write(str2 + "\n")
#         else:
#             print('#'*20)
#             return self.parse_url_utils(url2)
#
#
#     def file_to_file(self):
#         """
#         读取 url_all.txt, 解析后写入文件
#         :return:
#         """
#         with open(self.read_file_path) as f:
#             counter = 1
#             flag = False
#             last_one_url = ""
#             if os.path.exists(self.write_file_path):
#                 with open(self.write_file_path) as f2:
#                     last_one_url = f2.readlines()[-1].split('^')[3]
#             else:
#                 flag = True
#
#             for line in f.readlines():
#                 province = line.strip().split('^')[0]
#                 city = line.strip().split('^')[1]
#                 region = line.strip().split('^')[2]
#                 url = line.strip().split('^')[3]
#
#                 if last_one_url == url:
#                     flag = True
#                     continue
#
#                 if flag is True:
#                     print("开始解析第%d行, %s"%(counter, url))
#                     str2 = province + '^' + city + '^' + region + '^' + self.parse_url_utils(url)
#
#                     with open(self.write_file_path, "a+") as f2:
#                         f2.write(str2 + "\n")
#                     # print(url)
#                     # if counter%150 == 0:
#                     #     print("切换")
#                     #     spider_utils.change_ip()
#                     print("结束解析----------" + '\n')
#
#                     counter +=1
#
#
#     def kafka_to_file(self, args):
#         province = args.get('province')
#         city = args.get('city')
#         region = args.get('region')
#         url = args.get('url')
#
#         str2 = province + '^' + city + '^' + region + '^' + self.parse_url_utils(url)
#
#         with open(self.write_file_path, "a+") as f2:
#             f2.write(str2 + "\n")
#
# if __name__ == '__main__':
#     write_file_path1 = 'dianping_hangzhou_data_spa.txt'
#     read_file_path1 = '../spider_producer/url_all.txt'
#
#     dian_ping_consumer = DianPingConsumer(write_file_path1, read_file_path1)
#
#     # dian_ping_consumer.file_to_file()
#
#
#     res = dian_ping_consumer.parse_url_utils('http://www.dianping.com/shop/568037503')
#
#     print(res)
#
