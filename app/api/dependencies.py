from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import dw_mysql_client_manager, meta_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw_mysql_repository import DWMysqlRepository
from app.repositories.mysql.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.services.query_service import QueryService

#深度依赖注入
# 返回操作dw的session对象的函数
async def get_dw_session():
    async with dw_mysql_client_manager.session_factory() as session:
        yield session  # 不能用return 如果用return with会立即结束 session是立即关闭

# 返回操作meta的session对象的函数
async def get_meta_session():
    async with meta_mysql_client_manager.session_factory() as session:
        yield session


def get_query_servive(dw_session: AsyncSession = Depends(get_dw_session),
                      meta_session: AsyncSession = Depends(get_meta_session)
                      ) -> QueryService:
    return QueryService(
        dw_mysql_repository=DWMysqlRepository(dw_session),
        meta_mysql_repository=MetaMysqlRepository(meta_session),
        value_es_repository=ValueESRepository(es_client_manager.client),
        column_qdrant_repository=ColumnQdrantRepository(qdrant_client_manager.client),
        metric_qdrant_repository=MetricQdrantRepository(qdrant_client_manager.client),
        embedding_client=embedding_client_manager.client
    )
