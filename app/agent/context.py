from typing import TypedDict

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw_mysql_repository import DWMysqlRepository
from app.repositories.mysql.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class DataAgentContext(TypedDict):
    dw_mysql_repository: DWMysqlRepository
    meta_mysql_repository: MetaMysqlRepository
    value_es_repository: ValueESRepository
    column_qdrant_repository: ColumnQdrantRepository
    metric_qdrant_repository: MetricQdrantRepository
    embedding_client: HuggingFaceEndpointEmbeddings
