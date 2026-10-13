import json

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.agent.context import DataAgentContext
from app.agent.graph import compiled_graph
from app.agent.state import DataAgentState
from app.core.log import logger
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw_mysql_repository import DWMysqlRepository
from app.repositories.mysql.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class QueryService:
    def __init__(self,
                 dw_mysql_repository: DWMysqlRepository,
                 meta_mysql_repository: MetaMysqlRepository,
                 value_es_repository: ValueESRepository,
                 column_qdrant_repository: ColumnQdrantRepository,
                 metric_qdrant_repository: MetricQdrantRepository,
                 embedding_client: HuggingFaceEndpointEmbeddings
                 ):
        self.dw_mysql_repository = dw_mysql_repository
        self.meta_mysql_repository = meta_mysql_repository
        self.value_es_repository = value_es_repository
        self.column_qdrant_repository = column_qdrant_repository
        self.metric_qdrant_repository = metric_qdrant_repository
        self.embedding_client = embedding_client

    async def search(self, query: str):
        try:
            # 创建state对象
            """
            - 华北地区销售总额
            - 2025年各地区平均销售额
            - 各个地区iPhone去年卖了多少钱
            """
            # state = DataAgentState(query="各个地区iPhone去年卖了多少钱", fail_count=0)
            state = DataAgentState(query=query, fail_count=0)
            # state = DataAgentState(query="华北地区销售总额", fail_count=0)
            # 创建context对象
            context = DataAgentContext(
                dw_mysql_repository=self.dw_mysql_repository,
                meta_mysql_repository=self.meta_mysql_repository,
                value_es_repository=self.value_es_repository,
                column_qdrant_repository=self.column_qdrant_repository,
                metric_qdrant_repository=self.metric_qdrant_repository,
                embedding_client=self.embedding_client
            )

            # 运行图，输出自定义数据
            async for chunk in compiled_graph.astream(
                    input=state,
                    context=context,
                    stream_mode="custom"
            ):
                # chunk {'stage':"查询阶段"}
                # chunk {'result':"输出结果"}
                yield f'data:{json.dumps(chunk, ensure_ascii=False, default=str)}\n\n'
        except Exception as e:
            # 如果业务失败，回滚事务
            logger.error(f"查询失败: {str(e)}")
            #  {'error':"返回失败信息"}
            yield f'data:{json.dumps({"error": f"查询失败: {str(e)}"}, ensure_ascii=False, default=str)}\n\n'
