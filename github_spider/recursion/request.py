# -*- coding=utf8 -*-
import logging
import time

import grequests
import requests
from retrying import retry

from github_spider.const import (
    PROXY_KEY,
    HEADERS,
)
from github_spider.extensions import redis_client
from github_spider.settings import (
    TIMEOUT,
    REQUEST_RETRY_COUNT,
)
from github_spider.utils import get_proxy


LOGGER = logging.getLogger(__name__)


def request_with_proxy(url):
    for i in range(REQUEST_RETRY_COUNT):
        proxy = get_proxy()
        if not proxy:
            time.sleep(10 * 60)

        try:
            proxy_map = {'https': 'http://{}'.format(proxy.decode('ascii'))}
            redis_client.zincrby(PROXY_KEY, proxy)
            response = requests.get(url, proxies=proxy_map,
                                    headers=HEADERS, timeout=TIMEOUT)
        except Exception as exc:
            LOGGER.exception(exc)
            redis_client.zrem(PROXY_KEY, proxy)
        else:
            if response.status_code == 200:
                return response.json()


def exception_handler(request, exception):
    """
    :summary: 操作错误
    """
    proxy = request.kwargs.get('proxies', {}).get('https', '')[7:]
    redis_client.zrem(PROXY_KEY, proxy)
    LOGGER.error('request url:{} failed'.format(request.url))
    LOGGER.error('proxy: {}'.format(proxy))
    LOGGER.exception(exception)


@retry(stop_max_attempt_number=REQUEST_RETRY_COUNT,
       retry_on_result=lambda result: not result)
def async_get(urls):
    """
    :summary: 异步请求数据
    """
    rs = []
    for url in urls:
        proxy = get_proxy()
        if not proxy:
            time.sleep(10 * 60)

        proxy_map = {'https': 'http://{}'.format(proxy.decode('ascii'))}
        redis_client.zincrby(PROXY_KEY, proxy)
        rs.append(grequests.get(url, proxies=proxy_map,
                                headers=HEADERS, timeout=TIMEOUT))
    result = grequests.map(rs, exception_handler=exception_handler)
    return [x.json() for x in result if x]


def sync_get(urls):
    """
    :summary: 同步请求数据
    """
    result = []
    for url in urls:
        try:
            LOGGER.debug('get {}'.format(url))
            response = requests.get(url, headers=HEADERS)
            if not response.ok:
                LOGGER.info('get {} failed'.format(url))
                continue

            result.append(response.json())
            # response = request_with_proxy(url)
            # result.append(response)
        except Exception as exc:
            LOGGER.error('get {} fail'.format(url))
            LOGGER.exception(exc)
            continue
    return result
