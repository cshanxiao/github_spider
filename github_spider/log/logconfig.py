# -*- coding: utf8 -*-
u'''
@summary:
@author: cshanxiao
@date: 2016年7月3日
'''
import logging.config
from github_spider.common.config import LOG_CONFIG_FILE_PATH


logging.config.fileConfig(LOG_CONFIG_FILE_PATH)
log = logging.getLogger("root")
spider_log = logging.getLogger("spider")



