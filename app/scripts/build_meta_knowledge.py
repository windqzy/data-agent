"""
构建元知识库知识的同步脚本
"""
import asyncio

from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import meta_mysql_client_manager, dw_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.core.log import logger
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw_mysql_repository import DWMysqlRepository
from app.repositories.mysql.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.services.meta_knowledge_service import MetaKnowledgeService

"""
1.初始化所有的客户端
2.创建session对象
3.创建业务层对象 和 依赖的持久层对象
4.调用业务对象的build方法来构建
5.如果成功，提交事务，如果失败，回滚事务
6.无论成功还是失败，最终关闭所有客户端的连接
"""


# 启动构建的函数
async def start_build():
    logger.info(f'开始准备元知识库的构建')
    # 初始化所有的客户端
    dw_mysql_client_manager.init_client()
    meta_mysql_client_manager.init_client()
    es_client_manager.init_client()
    qdrant_client_manager.init_client()
    embedding_client_manager.init_client()
    try:
        # 创建session对象
        assert meta_mysql_client_manager.session_factory
        async with(
            dw_mysql_client_manager.session_factory() as dw_session,
            meta_mysql_client_manager.session_factory() as meta_session,
        ):
            # 创建业务层对象
            service = MetaKnowledgeService(
                dw_mysql_repository=DWMysqlRepository(dw_session),
                meta_mysql_repository=MetaMysqlRepository(meta_session),
                value_es_repository=ValueESRepository(es_client_manager.client),
                column_qdrant_repository=ColumnQdrantRepository(qdrant_client_manager.client),
                metric_qdrant_repository=MetricQdrantRepository(qdrant_client_manager.client),
                embedding_client=embedding_client_manager.client
            )

            # 调用业务对象的build方法来构建
            await service.build()
            # 如果业务成功完成，提交事务
            await dw_session.commit()  # dw库只做查询 可以不写着一行
            await meta_session.commit()
            logger.info(f'完成元知识库的构建')
    except Exception as e:
        # 如果业务失败，回滚事务
        logger.error(f'构建元知识库失败：{str(e)}')
        await meta_session.rollback()
        raise Exception(e)  # 显示完整的错误信息
    finally:
        # 无论成功还是失败最终都要关闭客户端
        await dw_mysql_client_manager.close_client()
        await meta_mysql_client_manager.close_client()
        await es_client_manager.close_client()
        await qdrant_client_manager.close_client()


if __name__ == "__main__":
    asyncio.run(start_build())
