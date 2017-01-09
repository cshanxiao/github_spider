# -*- coding: utf8 -*-
u'''
:summary:
:author: cshanxiao
:date: 2017年1月4日
'''
from github_spider.proxy.ip181 import get_proxy


if __name__ == '__main__':
    get_proxy(test_url="https://api.github.com/users/cshanxiao")