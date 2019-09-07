import asyncio
from pyppeteer import launch
import requests
from pyquery import PyQuery as pq
import time
import random
from bs4 import BeautifulSoup
from pyquery import PyQuery as pq
from cookie_pools.redis_helper import RedisHelper
from configparser import ConfigParser
import redis


cfg = ConfigParser()
cfg.read('../config/config.ini')


width, height = 1280, 800
class GetCookie(object):
    def __init__(self, url_file):
        self.url_file = url_file


    async def get_cookie(self, url1):
        browser = await launch(headless=False, autoClose=False, args=['--disable-infobars', f'--window-size={width},{height}'])
        page = await browser.newPage()
        await page.setViewport({'width': width, 'height': height})

        redis_client = redis.Redis(host=cfg.get('redis', 'host'), port=cfg.get('redis', 'port'))

        # await page.goto('http://www.dianping.com/shop/132022588')
        #
        # # await page.goto('http://quotes.toscrape.com/js/')
        # #
        # print(await page.content())


        # # 检测是否有滑块, 通过检测是否有相关的元素
        # slider = await page.Jeval('#yodaBox', 'node => node.style')
        #
        # if slider:
        #     print('出现滑块')
        #
        # else:
        #     print('没出现')


        with open(self.url_file, 'r') as f:
            key1 = 1
            for line in f.readlines():

                cookies_dict = dict()
                url = line.strip('\n').split('^')[3]
                await asyncio.sleep(1)

                await page.goto(url, {'waitUntil':'domcontentloaded'})

                cookies_list = await page.cookies()
                for cookies in cookies_list:
                    cookies_dict[cookies.get('name')] = cookies.get('value')

                print(cookies_dict)

                cookie_lxsdk_s = str(cookies_dict['_lxsdk_s'])

                # redis_client.set(key1, str(cookies_dict), ex=1200)


                if '_lxsdk_s' in cookies_dict.keys():
                    for counter in range(1, 50, 2):
                        print(cookies_dict)
                        cookies_dict['_lxsdk_s'] = cookie_lxsdk_s[:-1] + str(counter)
                        print(counter)
                        cookie = str(cookies_dict)
                        if cookie == '{}':
                            print('空')
                        else:
                            redis_client.set(key1, cookie, ex=1200)
                            key1 += 1


        # # --disable-infobars, 禁止提示
        # # window-size, 设置页面显示
        # browser = await launch(headless=False, autoClose=False, args=['--disable-infobars', f'--window-size={width},{height}'])
        #
        # page = await browser.newPage()
        #
        # await page.setViewport({'width': width, 'height': height})
        # await page.goto(url1, {'waitUntil':'domcontentloaded'}) # 不加这个参数会, 点评页面会加载很久
        #
        # print(await page.cookies())


if __name__ == '__main__':

    # asyncio.get_event_loop().run_until_complete(get_cookie('http://www.dianping.com/nanjing'))

    getcookie = GetCookie('../spider_producer/url_all.txt')

    asyncio.get_event_loop().run_until_complete(getcookie.get_cookie(''))
