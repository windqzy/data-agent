from app.conf.app_config import app_config
from qdrant_client import AsyncQdrantClient, models

from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant

"""
用于操作qdrant库的字段信息数据的持久层模块
"""


class ColumnQdrantRepository:
    collection_name = "data-agent-column_collection2"

    def __init__(self, client: AsyncQdrantClient):
        self.client = client

    async def _create_collection(self):
        client = self.client
        collection_name = self.collection_name
        # 如果已存在，先删除  =》 方便多次测试
        if await client.collection_exists(collection_name=collection_name):
            await client.delete_collection(collection_name=collection_name)
        await client.create_collection(
            collection_name=collection_name,  # 集合名称
            # 向量配置
            vectors_config=models.VectorParams(
                size=app_config.qdrant.embedding_size,  # 向量维度
                distance=models.Distance.COSINE  # 余弦相似度
            ),
        )

    # 批量插入多个带字段信息的向量
    async def insert_column_vectors(self, ids: list[str], payloads: list[ColumnInfoQdrant], vectors: list[list[float]]):
        # 创建集合（用来存储向量）  如果存在先删除 =》 测试阶段使用
        await self._create_collection()

        # 分批次的批量插入多个向量
        batch_size = 10
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i + batch_size]
            batch_payloads = payloads[i:i + batch_size]
            batch_vectors = vectors[i:i + batch_size]

            await self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=batch_ids[i],
                        payload=batch_payloads[i],
                        vector=batch_vectors[i],
                    )
                    for i in range(len(batch_ids))
                ],
            )

    # 搜索
    async def search(self, keyword_vector: list[float]) -> list[ColumnInfoQdrant]:
        client = self.client
        collection_name = self.collection_name
        # 搜索
        result = await client.query_points(
            collection_name=collection_name,
            query=keyword_vector,
            score_threshold=0.6  # 相似度的最小值
        )

        # print(result.points)
        # for point in result.points:
        #     print(point.payload)

        return [ColumnInfoQdrant(**item.payload) for item in result.points]
