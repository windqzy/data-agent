import asyncio
from random import random
from typing import Optional

from huggingface_hub.utils import validate_repo_id
from qdrant_client import AsyncQdrantClient, models
from app.conf.app_config import app_config
from app.conf.app_config import QdrantConfig


class QdrantClientManager:
    def __init__(self, config: QdrantConfig):
        self.config = config
        self.client: Optional[AsyncQdrantClient] = None

    def init_client(self):
        self.client = AsyncQdrantClient(
            f'http://{self.config.host}:{self.config.port}'
        )

    async def close_client(self):
        await self.client.close()


qdrant_client_manager = QdrantClientManager(app_config.qdrant)

if __name__ == "__main__":
    async def test():

        qdrant_client_manager.init_client()
        client = qdrant_client_manager.client
        collection_name = 'my_collection'
        # 创建集合 只有不存在才创建
        if not await client.collection_exists(collection_name=collection_name):
            await client.create_collection(
                collection_name=collection_name,  # 集合名称
                # 向量配置
                vectors_config=models.VectorParams(
                    size=1024,  # 向量的维度
                    distance=models.Distance.COSINE  # 余弦相似度
                )
            )
        # 创建集合 如果存在先删除，测试阶段使用
        if await client.collection_exists(collection_name=collection_name):
            await client.delete_collection(collection_name=collection_name)
        await client.create_collection(
            collection_name=collection_name,
            # 向量配置
            vectors_config=models.VectorParams(
                size=1024,  # 向量的维度
                distance=models.Distance.COSINE  # 余弦相似度
            )
        )

        # 批量插入多个向量
        await client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=i,
                    payload={
                        'color': 'red' if i % 2 == 0 else 'green',
                    },
                    vector=[
                        random() for _ in range(1024)
                    ]
                )
                for i in range(10)
            ]
        )

        # 搜索
        result = await client.query_points(
            collection_name=collection_name,
            query=[random() for _ in range(1024)],
            query_filter=models.Filter(  # 根据payload数据进行过了
                must=[models.FieldCondition(key='color', match=models.MatchValue(value='red'))],
            ),
            limit=5,
            score_threshold=0.7,
            with_vectors=True
        )

        print(result.points)
        for point in result.points:
            print(point.payload)

        await qdrant_client_manager.close_client()


    asyncio.run(test())
