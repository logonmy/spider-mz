import redis
from configparser import ConfigParser
from utils import selenium_utils
import time
from pyppeteer import launch
import asyncio
import random

cfg = ConfigParser()
cfg.read('../config/config.ini')


width, height = 1280, 800
class RedisHelper(object):
    def __init__(self):
        self.redis_client = redis.Redis(host=cfg.get('redis', 'host'), port=cfg.get('redis', 'port'))

    def get(self, key):
        return self.redis_client.get(key)

    def get_random_key(self):
        return self.redis_client.randomkey()

    def get_random_record(self):
        random_key = self.get_random_key()
        value = self.get(random_key)
        return {b'key':random_key, b'value':value}

    def get_max_key(self):
        all_keys = self.redis_client.keys()
        if len(all_keys) == 0:
            return 1
        else:
            keys_int = [int(key) for key in all_keys]
            return max(keys_int)

    def set_cookie(self):
        """
        设置过期时间,时间过后,key value都会删除
        :return:
        """
        with open('../spider_producer/url_all.txt') as f:
            key1 = self.get_max_key()
            for url in f.readlines():
                # time.sleep(1)

                cookie_list = selenium_utils.no_delay_cookies(url.strip('\n').split('^')[3])

                if '_lxsdk_s' in cookie_list.keys():
                    for counter in range(0, 30, 2):

                        cookie_list['_lxsdk_s'] = cookie_list.get('_lxsdk_s')[0: (cookie_list.get('_lxsdk_s').index('C') + 1)] + str(counter)

                        # cookie_list['_lxsdk_s'] = str(cookie_list['_lxsdk_s'])[:-1] + str(counter)

                        cookie = str(cookie_list)
                        if cookie == '{}':
                            print('空')
                        else:
                            print(cookie)
                            self.redis_client.set(key1, cookie, ex=600)
                            key1 += 1

    def set_value(self):
        self.redis_client.set('key2', 'hello', ex=10)

    async def set_cookie_by_pyppeteer(self):
        """
        通过文件的方式
        设置过期时间,时间过后,key value都会删除
        :return:
        """
        browser = await launch(headless=False, autoClose=False, args=['--disable-infobars',
                                                                      f'--window-size={width},{height}',
                                                                      '--proxy-server=113.57.56.117:32982',
                                                                      '--proxy-server=113.57.56.117:32982'
                                                                      ])

        page = await browser.newPage()
        await page.setViewport({'width': width, 'height': height})

        with open('../spider_producer/url_page.txt') as f:

            key1 = self.get_max_key()
            for url in f.readlines():
                # await page.deleteCookie()

                await page._client.send('Network.clearBrowserCookies')

                cookie_dict = dict()

                await asyncio.sleep(2)

                # time.sleep(1)
                url_final = url.strip('\n').split('^')[3]

                await page.goto(url_final, {'waitUntil':'domcontentloaded'})

                content = await page.content()
                title = await page.title()

                if title == '验证中心':
                    print('需要验证---------')
                    await asyncio.sleep(3)
                    print(await page.content())
                    await page.hover('#yodaMoveingBar')
                    await page.mouse.down()

                    # await page.mouse.move(750, 0, {'steps': 9})
                    await page.mouse.move(random.randint(760, 850), 0, {'steps': random.randint(8,12)})
                    await page.mouse.up()

                cookie_list_all = await page.cookies()
                for cookie_list_dict in cookie_list_all:
                    cookie_dict[cookie_list_dict.get('name')] = cookie_list_dict.get('value')

                # if '_lxsdk_s' in cookie_list.keys():
                #     for counter in range(1, 200, 3):
                #         cookie_list['_lxsdk_s'] = str(cookie_list['_lxsdk_s'])[:-1] + str(counter)
                #
                #         cookie = str(cookie_list)
                #         if cookie == '{}':
                #             print('空')
                #         else:
                #             self.redis_client.set(key1, cookie, ex=600)
                #             key1 += 1

                cookie_dict_keys = cookie_dict.keys()
                if '_lxsdk_s' in cookie_dict_keys and len(cookie_dict_keys)>2:
                    # print(cookie_dict)
                    # cookie = str(cookie_dict)
                    # if cookie == '{}':
                    #     print('空')
                    # else:
                    #     self.redis_client.set(key1, cookie, ex=1200)
                    #     key1 += 1

                    cookie = str(cookie_dict)
                    print(cookie)
                    self.redis_client.set(key1, cookie, ex=2400)
                    key1 += 1

            await page.close()

    def del_record(self, key):
        self.redis_client.delete(key)

if __name__ == '__main__':
    r = RedisHelper()
    # r.set_cookie()
    asyncio.get_event_loop().run_until_complete(r.set_cookie_by_pyppeteer())


