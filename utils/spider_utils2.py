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


cfg = ConfigParser()
cfg.read('../config/config.ini')

class SpiderUtils(object):
    def __init__(self, dp_increase_id, ip_proxy_host, ssh_ip):
        # 如果 cookie_id文件不存在, 则新建
        if not os.path.exists(dp_increase_id):
            with open(dp_increase_id, 'w') as f1:
                f1.write('3')

        self.dp_increase_id = dp_increase_id
        self.ip_proxy_host = ip_proxy_host
        self.ssh_ip = ssh_ip


    def requests_dp(self, url):
        # 动态加载 user_agent
        user_agent = ["Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1 Safari/605.1.15"]

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
        with open(self.dp_increase_id, 'r') as f2:
            increase_cookie_id = int(f2.read())
        with open(self.dp_increase_id, 'w') as f3:
            f3.write(str(increase_cookie_id + 3))

        # 获取最新的IP地址
        with open(self.ip_proxy_host) as f4:
            all_ip = ""
            try:
                all_ip = f4.readlines()
            except Exception as e:
                print(e)

            new_ip = all_ip[-1].strip()

            if new_ip.find("重复IP") == 0:
                new_ip = self.change_ip()

            ip_res = self.test_ip(new_ip)
            cookies = eval(str(all_ip[1]).strip("\n"))
            if '_lxsdk_s' in cookies.keys():
                cookies['_lxsdk_s'] = str(cookies['_lxsdk_s'])[:-1] + str(increase_cookie_id)
                print("cookies-----", cookies)
                print(cookies['_lxsdk_s'])

            if ip_res !=0:
                print("该IP无效重试 ", new_ip)
                self.change_ip()
                self.requests_dp(url)
            else:
                print("该IP有效 ", new_ip)
                retry_times = 0
                while retry_times < 3:

                    ip_dict = {
                        'http': 'http://%s:32982'% new_ip,
                        'https': 'http://%s:32982'% new_ip
                    }

                    proxies = [ip_dict]
                    proxy_ip = random.choice(proxies)

                    print(proxy_ip)
                    try:
                        # 休眠
                        # sleep_time = random.uniform(3, 9)
                        # print("休眠", sleep_time)
                        # time.sleep(sleep_time)

                        # sleep_time = random.uniform(2, 4)
                        # print("休眠", sleep_time)
                        # time.sleep(sleep_time)

                        print("---335555---", cookies)

                        response = requests.get(url, headers=headers, proxies=proxy_ip, timeout=10, cookies=cookies)

                        print("-"*20)
                        print(response.headers)
                        print(response.request.headers)
                        print("-"*20)

                        return response
                    except requests.exceptions.ConnectionError as e:
                        retry_times = retry_times + 1
                        # print("重试第%d"%retry_times,"报错了", e)
                    except requests.exceptions.ReadTimeout as e:
                        retry_times = retry_times + 1
                        # print("重试第%d"%retry_times,"报错了", e)
                return None


    def change_ip(self):
        ip_port = self.ssh_ip.split(':') # 获取VPS登录方式

        start_time = datetime.datetime.now()
        command_linux = "ssh root@%s -p%s 'sh restart_pp.sh'"%(ip_port[0], ip_port[1])

        str1 = os.popen(command_linux)
        res_ip = str1.read()
        end_time = datetime.datetime.now()

        cost_time = end_time - start_time

        with open(self.ip_proxy_host) as f_r:
            all_ip = f_r.read()
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


if __name__ == '__main__':
    cc = cfg.get('proxy_host', 'host1')
    print(cc)
    ss = SpiderUtils('../config/2222.txt', '', cc)
    ss.change_ip()