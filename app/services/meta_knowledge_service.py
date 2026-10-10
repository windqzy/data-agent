from typing import Any

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.conf.meta_config import meta_config, TableConfig, MetricConfig
from app.core.log import logger
from app.models.mysql.column_info_mysql import ColumnInfoMySQL
from app.models.mysql.column_metric_mysql import ColumnMetricMySQL
from app.models.mysql.metric_info_mysql import MetricInfoMySQL
from app.models.mysql.table_info_mysql import TableInfoMySQL
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw_mysql_repository import DWMysqlRepository
from app.repositories.mysql.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class MetaKnowledgeService:
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

    """
    1.处理表和字段相关数据
    1.1 将表信息和字段信息保存到meta库
    1.2 将字段信息保存到qdrant库建立向量索引
    1.3 将字段值信息保存到es库建立全文索引
    2.处理指标相关数据
    2.1将指标信息保存到meta库
    2.2将指标信息保存到qdrant建立向量索引
    
    """

    # 构建元数据知识库的业务方法
    async def build(self):
        # 1.处理表和字段相关数据
        # 1.1将表信息和字段信息保存到meta库
        column_infos: list[ColumnInfoMySQL] = await self._save_table_infos_to_mata(meta_config.tables)
        logger.info(f"将表信息和字段信息保存到meta库完成")
        # 1.2 将字段信息保存到qdrant库建立向量索引
        await self._save_column_infos_to_qdrant(column_infos)
        logger.info(f"将字段信息保存到qdrant库建立向量索引")
        # 1.3将字段值信息保存到es库建立全文索引
        await self._save_column_value_infos_to_es(column_infos, meta_config.tables)
        logger.info(f"将字段信息保存到qdrant库建立向量索引")
        # 2.处理指标相关数据
        # 2.1将指标信息保存到meta库
        metrics_infos: list[MetricInfoMySQL] = await self._save_metric_infos_to_meta(meta_config.metrics)
        logger.info(f"将指标信息保存到meta库")
        # 2.2将指标信息保存到qdrant建立向量索引
        await self._save_metric_infos_to_qdrant(metrics_infos)
        logger.info(f"将指标信息保存到qdrant建立向量索引")

    async def _save_table_infos_to_mata(self, tables: list[TableConfig]) -> list[ColumnInfoMySQL]:
        # 1.遍历tables准备表信息列表和字段信息列表
        table_infos: list[TableInfoMySQL] = []
        column_infos: list[ColumnInfoMySQL] = []
        for table in tables:
            table_infos.append(TableInfoMySQL(id=table.name,
                                              name=table.name,
                                              role=table.role,
                                              description=table.description
                                              ))
            # 查询当前表所有字段的类型 dict[字段名称，字段类型名]
            column_types: dict[str, str] = await self.dw_mysql_repository.get_column_types(table.name)
            # 查询当前表
            for column in table.columns:
                # 查询当前字段的前十个值
                examples: list[Any] = await self.dw_mysql_repository.get_column_examples(table.name, column.name)
                column_infos.append(ColumnInfoMySQL(
                    id=f'{table.name}.{column.name}',
                    name=column.name,
                    type=column_types[column.name],  # 需要查询dw
                    role=column.role,
                    description=column.description,
                    examples=examples,  # 需要查询dw库
                    alias=column.alias,
                    table_id=table.name
                ))

        # 2.将表信息列表和字段信息列表保存到meta库
        self.meta_mysql_repository.save_table_infos(table_infos)
        self.meta_mysql_repository.save_column_infos(column_infos)
        return column_infos


    async def _save_column_infos_to_qdrant(self, column_infos):
        pass

    async def _save_column_value_infos_to_es(self, column_infos, tables):
        pass

    async def _save_metric_infos_to_meta(self, metrics: list[MetricConfig]) -> list[MetricInfoMySQL]:
        # 1.遍历metrics来手机指标信息列表和字段指标信息列表
        metric_infos: list[MetricInfoMySQL] = []
        column_metrics: list[ColumnMetricMySQL] = []

        for metric in metrics:
            metric_infos.append(MetricInfoMySQL(id=metric.name,
                                                name=metric.name,
                                                description=metric.description,
                                                relevant_columns=metric.relevant_columns,
                                                alias=metric.alias
                                                ))
            for column_id in metric.relevant_columns:
                column_metrics.append(ColumnMetricMySQL(column_id=column_id,
                                                        metric_id=metric.name))

        # 2.将指标信息列表和字段指标列表保存到meta库
        self.meta_mysql_repository.save_metric_infos(metric_infos)
        self.meta_mysql_repository.save_column_metrics(column_metrics)
        return metric_infos
        """
        得到：
        metric_info 表
        name	  description	relevant_columns
        GMV	       交易总额	    order_amount, pay_amount
        AOV	       平均订单金额	order_amount, order_id
        
        
        得到：
        column_metric 表
        column_id	      metric_id
        order_amount	    GMV
        pay_amount	        GMV
        order_amount	    AOV
        order_id	        AOV
        """

    async def _save_metric_infos_to_qdrant(self, metrics_infos: list[MetricInfoMySQL]):
        pass
