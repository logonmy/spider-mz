# -*- coding:utf-8 -*-
import datetime
import logging.config
import os
import random
import socket
import time
import requests
from configparser import ConfigParser
from utils import selenium_utils
from cookie_pools import redis_helper
import random
from pyppeteer import launch
import asyncio


cfg = ConfigParser()
cfg.read('../config/config.ini')

width, height = 1280, 800
class SpiderUtils(object):
    def __init__(self, ip_proxy_host, ssh_ip):
        # self.dp_increase_id = dp_increase_id
        self.ip_proxy_host = ip_proxy_host
        self.ssh_ip = ssh_ip
        # self.redis_client = redis_helper.RedisHelper()
        # # 如果 dp_increase_id 文件不存在, 则新建
        # if not os.path.exists(dp_increase_id):
        #     with open(dp_increase_id, 'w') as f1:
        #         f1.write('3')
        #
        # if not os.path.exists(ip_proxy_host):
        #     open(ip_proxy_host, 'w').close()
        #     self.change_ip_cookies()

    def requests_dp(self, url1, cookies):
        print('当前url  ', url1)
        # print('34---加载', self.ip_proxy_host)
        # 动态加载 user_agent
        # user_agent = ["Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1 Safari/605.1.15",
        #               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
        #               'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
        #               'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:68.0) Gecko/20100101 Firefox/68.0',
        #                 ]

        # 公司笔记本
        user_agent = ["Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3494.0 Safari/537.36",
                      ]

        # # 自己
        # user_agent = ["Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3494.0 Safari/537.36",
        #               ]



        # 封装请求头
        headers = dict()
        headers['User-Agent'] = random.choice(user_agent)
        headers["Connection"] = "keep-alive"
        headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        headers["Accept-Encoding"] = "gzip, deflate"
        headers["Accept-Language"] = "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7"
        headers["Host"] = "www.dianping.com"
        headers["Accept-Language"] = "zh-cn"
        headers["Upgrade-Insecure-Requests"] = "1"
        headers["Cache-Control"] = "max-age=0"

        # 获取自增 cookie
        # with open(self.dp_increase_id, 'r') as f2:
        #     increase_cookie_id = int(f2.read())
        #     print('53--当前cookie', increase_cookie_id)
        # with open(self.dp_increase_id, 'w') as f3:
        #     f3.write(str(increase_cookie_id + 3))

        # 获取最新的IP地址
        with open(self.ip_proxy_host) as f4:
            all_ip = ""
            try:
                all_ip = f4.readlines()
            except Exception as e:
                print(e)

            new_ip = all_ip[-1].strip()

            if new_ip.find("重复IP") == 0:
                self.change_ip()
                return self.requests_dp(url1, cookies)

            ip_res = self.test_ip(new_ip)

            # cookies = eval(str(all_ip[0]).strip("\n"))

            # print('74---当前ip-cookie', new_ip, cookies)
            #
            # if '_lxsdk_s' in cookies.keys():
            #     cookies['_lxsdk_s'] = str(cookies['_lxsdk_s'])[:-1] + str(increase_cookie_id)
            #     # print("cookies-----", cookies)
            #     # print(cookies['_lxsdk_s'])

            if ip_res !=0:
                # print("该IP无效重试 ", new_ip)
                self.change_ip()
                return self.requests_dp(url1, cookies)
            else:
                # print("该IP有效 ", new_ip)
                retry_times = 0
                while retry_times < 3:
                    ip_dict = {
                        'http': 'http://%s:32982'% new_ip,
                        'https': 'http://%s:32982'% new_ip
                    }

                    proxies = [ip_dict]
                    proxy_ip = random.choice(proxies)

                    print('ip-- ', proxy_ip)
                    try:
                        response = requests.get(url1, headers=headers, proxies=proxy_ip, timeout=10, cookies=cookies)

                        if response.text.find('é¡µé¢ä¸å­å¨ | ç¾å¢ç¹è¯') != -1:
                            print('-----------11122224444')
                            print(response.text)
                            cccc = asyncio.get_event_loop().run_until_complete(self.get_page_by_pyppeteer(url1, new_ip, cookies))

                            # return self.requests_dp(url1, cookies)

                            # response1 = requests.get(url1, headers=headers, proxies=proxy_ip, timeout=10, cookies=cookies)
                            #
                            # print('---------1333333')
                            # print(response1.text)
                            return cccc

                        else:
                            return response
                        # print("-"*20)
                        # print(response.headers)
                        # print(response.request.headers)
                        # print("-"*20)

                    except requests.exceptions.ConnectionError as e:
                        retry_times = retry_times + 1
                        # print("重试第%d"%retry_times,"报错了", e)
                    except requests.exceptions.ReadTimeout as e:
                        retry_times = retry_times + 1
                        # print("重试第%d"%retry_times,"报错了", e)
                return None

    def change_ip_cookies(self, url1='http://www.dianping.com/shop/98394949'):
        start_time = datetime.datetime.now()

        # 切换IP并解析
        ip_port = self.ssh_ip.split(':') # 获取VPS登录方式
        command_linux = "ssh root@%s -p%s 'sh restart_pp.sh'"%(ip_port[0], ip_port[1])
        str1 = os.popen(command_linux)
        res_ip = str1.read()

        # 耗时
        end_time = datetime.datetime.now()
        cost_time = end_time - start_time

        # 生成cookies
        cookies = selenium_utils.no_delay_cookies(url1)

        # 新生成的IP和Cookie写入文件
        repeat_flag = False
        with open(self.ip_proxy_host, 'r+') as f_r:
            # ip_gen = "60.178.91.229"
            all_content = f_r.read()
            #
            if all_content.find(res_ip) == -1:
                f_r.seek(0, 0) # get to the first position
                f_r.write(str(cookies).rstrip("\r\n") + "\n" + all_content + str(res_ip))
                print("更换IP Cookie,耗时", cost_time, res_ip, cookies)
                return res_ip
            else:
                print("重复IP: " + res_ip)
                f_r.write("重复IP: " + res_ip)
                repeat_flag = True

        # 如果重复则更换IP
        if repeat_flag is True:
            self.change_ip()

    def change_ip(self):
        ip_port = self.ssh_ip.split(':') # 获取VPS登录方式

        # print(ip_port)
        start_time = datetime.datetime.now()
        command_linux = "ssh root@%s -p%s 'sh restart_pp.sh'"%(ip_port[0], ip_port[1])

        str1 = os.popen(command_linux)
        res_ip = str1.read()
        end_time = datetime.datetime.now()

        cost_time = end_time - start_time

        with open(self.ip_proxy_host) as f_r:
            all_ip = f_r.read()
            # print(all_ip, res_ip)
            if all_ip.find(res_ip) == -1:
                with open(self.ip_proxy_host, "a+") as f_w:
                    f_w.write(res_ip)
                    print("更换IP,耗时", cost_time, res_ip)
                    return res_ip
            else:
                with open(self.ip_proxy_host, "a+") as f_w:
                    f_w.write("重复IP: " + res_ip)
                self.change_ip()

    @staticmethod
    def test_ip(ip_address):
        """
        测试该 IP + Port 是否有效
        :return: 0 代表有效
        """
        print("490,测试IP", ip_address)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        try:
            ip_result = sock.connect_ex((ip_address, 32982))
        except Exception as e:
            ip_result = -1
            print(e)
        # if ip_result == 0:
        #     print("Port is open")
        # else:
        #     print("Port is not open")

        return ip_result

    async def get_page_by_pyppeteer(self, url_final, ip_add, cookie):
        browser = await launch(headless=False, autoClose=False, args=['--disable-infobars',
                                                                      f'--window-size={width},{height}',
                                                                      '--proxy-server=%s:32982'%(ip_add,),
                                                                      '--proxy-server=%s:32982'%(ip_add,)
                                                                      ])
        page = await browser.newPage()
        await page.setViewport({'width': width, 'height': height})


        # await page.setCookie(cookie)


        await page.goto(url_final, {'waitUntil':'domcontentloaded'})
        title = await page.title()

        if title == '验证中心':
            print('需要验证---------')
            await asyncio.sleep(12)
            # print(await page.content())
            await page.hover('#yodaMoveingBar')
            await page.mouse.down()
            await page.mouse.move(random.randint(760, 850), 0, {'steps': random.randint(8,12)})
            await page.mouse.up()
        # print(await page.content())
        # await asyncio.sleep(3)

        return await page.content()