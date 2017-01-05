# -*- coding=utf8 -*-
u"""
:summary: 从网上爬取HTTPS代理
"""
import re
import time

from pyquery import PyQuery
import requests

from github_spider.const import PROXY_KEY
from github_spider.extensions import redis_client
from github_spider.settings import PROXY_USE_COUNT


def ProxyIp181():
    u"""
    :summary: 获取HTTPS代理，http://www.ip181.com/
    """
    content = requests.get('http://www.ip181.com/').content.decode('gb2312')
    pq = PyQuery(content)

    proxy_list = []
    for tr in pq("tr"):
        element = [PyQuery(td).text() for td in PyQuery(tr)("td")]
        if 'HTTPS' not in element[3]:
            continue

        result = re.search(r'\d+\.\d+', element[4], re.UNICODE)
        if result and float(result.group()) > 5:
            continue
        proxy_list.append((element[0], element[1]))

    return proxy_list

def get_proxy():
    while True:
        try:
            proxies = ProxyIp181()
            redis_client.zremrangebyscore(PROXY_KEY, PROXY_USE_COUNT, 10000)

            for host, port in proxies:
                address = '{}:{}'.format(host, port)
                print(address)
                if redis_client.zscore(PROXY_KEY, address) is None:
                    redis_client.zadd(PROXY_KEY, address, 0)
        except Exception, e:
            print e
        finally:
            time.sleep(10 * 60)
