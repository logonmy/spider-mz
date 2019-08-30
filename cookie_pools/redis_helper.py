import redis
from configparser import ConfigParser
from utils import selenium_utils
import time

cfg = ConfigParser()
cfg.read('../config/config.ini')

class RedisHelper(object):
    def __init__(self):
        self.redis_client = redis.Redis(host=cfg.get('redis', 'host'), port=cfg.get('redis', 'port'))

    def get(self, key):
        return self.redis_client.get(key)

    def get_random_key(self):
        return self.redis_client.randomkey()

    def random_get(self):
        return self.get(self.get_random_key())

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
                    for counter in range(1, 200, 3):
                        cookie_list['_lxsdk_s'] = str(cookie_list['_lxsdk_s'])[:-1] + str(counter)

                        cookie = str(cookie_list)
                        if cookie == '{}':
                            print('空')
                        else:
                            self.redis_client.set(key1, cookie, ex=600)
                            key1 += 1

    def set_value(self):
        self.redis_client.set('key2', 'hello', ex=10)


if __name__ == '__main__':
    # host = cfg.get('redis', 'host')
    # port = cfg.get('redis', 'port')
    #
    # print(host, port)

    r = RedisHelper()
    # r.set()

    # for i in range(10):
    #     print(r.random_get())

    r.set_cookie()
