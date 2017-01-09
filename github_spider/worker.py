# -*- coding=utf8 -*-
from celery import Celery
from github_spider.const import MongodbCollection
from github_spider.settings import CELERY_BROKER_URI
from github_spider.extensions import mongo_db

app = Celery('write_mongo', broker=CELERY_BROKER_URI)


@app.task
def mongo_save_entity(entity, collection_name):
    """
    :summary: 把数据写入mongo
    :Args:
        entity (dict): 数据
        collection_name: 数据集名称
    """
    mongo_collection = mongo_db[str(collection_name)]
    mongo_collection.update({'id': entity['id']}, entity, upsert=True)


@app.task
def mongo_save_relation(entity, relation_type):
    """
    :summary: 把用户与用户或用户与项目的关系写入mongo
    :Args:
        entity (dict): 数据
        relation_type (bool): 关系类型
    """
    mongo_collection = mongo_db[relation_type]
    data = mongo_collection.find_one({'id': entity['id']})
    if not data:
        mongo_collection.insert(entity)
    else:
        origin_list = entity['list']
        new_list = data['list']
        data['list'] = list(set(origin_list) | set(new_list))
        mongo_collection.update({'id': entity['id']}, data)
