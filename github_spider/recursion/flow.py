# -*- coding=utf8 -*-
"""
:summary: 流程控制
"""
from github_spider.const import (
    REDIS_VISITED_URLS,
    MongodbCollection,
)
from github_spider.extensions import redis_client
from github_spider.log.logconfig import spider_log as log
from github_spider.utils import (
    gen_user_repo_url,
    gen_user_following_url,
    gen_user_follwer_url,
    gen_url_list,
    gen_user_page_url,
    check_url_visited,
)
from github_spider.worker import (
    mongo_save_entity,
    mongo_save_relation,
)


def request_api(urls, method, callback, **kwargs):
    """
    :summary: 请求API数据
    :Args:
        urls (list): 请求url列表
        method (func): 请求方法
        callback (func): 回调函数
    """
    unvisited_urls = check_url_visited(urls)
    if not unvisited_urls:
        return

    try:
        bodies = method(unvisited_urls)
    except Exception as exc:
        log.exception(exc)
    else:
        redis_client.sadd(REDIS_VISITED_URLS, *unvisited_urls)
        map(lambda body: callback(body, method, **kwargs), bodies)


def parse_user(user, method):
    """
    :summary: 解析用户数据
    :Args:
        data (dict): 用户数据
        method (func): 请求方法
    """
    if not user:
        return

    user_id = user.get('login')
    if not user_id:
        return

    mongo_save_entity.delay(user, MongodbCollection.USER)
    follower_urls = gen_url_list(user_id, gen_user_follwer_url,
                                 user['followers'])
    following_urls = gen_url_list(user_id, gen_user_following_url,
                                  user['following'])
    repo_urls = gen_url_list(user_id, gen_user_repo_url, user.get('repos_count'))

    request_api(repo_urls, method, parse_repos, user=user_id)
    
    request_api(following_urls, method, parse_follow,
                user=user_id, kind=MongodbCollection.FOLLOWING)
    
    request_api(follower_urls, method, parse_follow,
                user=user_id, kind=MongodbCollection.FOLLOWER)


def parse_repos(data, method, user=None):
    """
    :summary: 解析项目数据
    :Args:
        data (list): 用户数据
        method (func): 请求函数
        user (string): 用户
    """
    if not data:
        return

    user = user or data[0].get('owner', {}).get('login')
    if not user:
        return

    repo_list = []
    for element in data:
        # fork的项目不关心
        if element.get('fork'):
            continue
        mongo_save_entity.delay(element, MongodbCollection.REPO_DETAIL)
    mongo_save_relation.delay({'id': user, 'list': repo_list},
                              MongodbCollection.USER_REPO)


def parse_follow(data, method, kind=MongodbCollection.FOLLOWER, user=None):
    """
    :summary: 解析关注关系
    :Args:
        data (list): 请求数据
        method (func): 请求函数
        kind (string): 是关注的人还是关注着
        user (string): 用户
    """
    if not data or not user:
        return

    users = []
    urls = []
    for element in data:
        users.append(element.get('login'))
        urls.append(gen_user_page_url(element.get('login')))

    mongo_save_relation.delay({'id': user, 'list': users}, kind)
    request_api(urls, method, parse_user)
