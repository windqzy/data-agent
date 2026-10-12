from elasticsearch import AsyncElasticsearch

from app.models.es.value_info_es import ValueInfoES

"""
用来操作es数据库中的字段值数据的持久层模块
"""


class ValueESRepository:
    index_name = "data-agent-value_index2"
    mappings = {
        "dynamic": False,
        "properties": {
            "id": {"type": "keyword"},
            "value": {"type": "text", "analyzer": "ik_max_word", "search_analyzer": "ik_max_word"},
            "type": {"type": "keyword"},
            "column_id": {"type": "keyword"},
            "column_name": {"type": "keyword"},
            "table_id": {"type": "keyword"},
            "table_name": {"type": "keyword"},
        }
    }

    def __init__(self, client: AsyncElasticsearch):
        self.client = client

    # 确保创建索引库
    async def _create_index(self):
        client = self.client
        index_name = self.index_name
        # 创建索引
        if await client.indices.exists(index=index_name):
            await client.indices.delete(index=index_name)
        await client.indices.create(
            index=index_name,
            mappings=self.mappings
        )

    # 保存多个字段值信息列表
    async def insert_value_infos(self, value_infos: list[ValueInfoES]):
        client = self.client
        index_name = self.index_name
        # 创建索引
        await self._create_index()

        # 遍历value_infos收集operations
        operations: list = []
        for value_info in value_infos:
            operations.append({
                "index": {
                    "_index": index_name
                }
            })
            operations.append(value_info)

        # 分批次的批量插入多个文档
        batch_size = 100
        for i in range(0, len(operations), batch_size):
            batch_operations = operations[i:i + batch_size]

            # 批量插入多个文档
            await client.bulk(
                operations=batch_operations
                # refresh=True, # 自动刷新  每插入一个文档就刷新一下  性能低
            )

        # 它不是把尚未保存的数据写入磁盘，而是让已经写入 Elasticsearch 的文档变得可以被搜索。
        await client.indices.refresh(index=index_name)
