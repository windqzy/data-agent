from elasticsearch import AsyncElasticsearch

"""
用来操作es数据库中的字段值数据的持久层模块
"""


class ValueESRepository:
    def __init__(self, client: AsyncElasticsearch):
        self.client = client
