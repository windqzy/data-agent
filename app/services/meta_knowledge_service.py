import uuid
from typing import Any

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.conf.meta_config import meta_config, TableConfig, MetricConfig
from app.core.log import logger
from app.models.es.value_info_es import ValueInfoES
from app.models.mysql.column_info_mysql import ColumnInfoMySQL
from app.models.mysql.column_metric_mysql import ColumnMetricMySQL
from app.models.mysql.metric_info_mysql import MetricInfoMySQL
from app.models.mysql.table_info_mysql import TableInfoMySQL
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant
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
                examples: list[Any] = await self.dw_mysql_repository.get_column_values(table.name, column.name)
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

    async def _save_column_infos_to_qdrant(self, column_infos: list[ColumnInfoMySQL]):
        # 遍历column_infos收集生成ids pyloads texts(name/description/alia)
        # 先收集生成一个list[dict(id/payload/text)]
        temp_list: list[dict] = []
        for column_info in column_infos:
            payload = ColumnInfoQdrant(
                id=column_info.id,
                name=column_info.name,
                type=column_info.type,
                role=column_info.role,
                examples=column_info.examples,
                description=column_info.description,
                alias=column_info.alias,
                table_id=column_info.table_id
            )
            # name
            temp_list.append({
                'id': uuid.uuid4(),
                'text': column_info.name,
                'payload': payload
            })

            # description
            temp_list.append({
                'id': uuid.uuid4(),
                'text': column_info.description,
                'payload': payload
            })

            # alias中的每个alia
            for alia in column_info.alias:
                temp_list.append({
                    'id': uuid.uuid4(),
                    'text': alia,
                    'payload': payload
                })

        ids: list[str] = [item['id'] for item in temp_list]
        payloads: list[str] = [item['payload'] for item in temp_list]
        texts: list[str] = [item['text'] for item in temp_list]
        # 对texts进行批量生成向量=>vectors
        batch_size = 16
        vectors: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_vectors: list[list[float]] = await self.embedding_client.aembed_documents(batch_texts)
            vectors.extend(batch_vectors)

        # 调用持久层保存字段信息列表ids payloads vectors
        await self.column_qdrant_repository.insert_column_vectors(ids, payloads, vectors)

    """
        我们只看一个字段，你就明白了。
        
        假设 MySQL 有一个字段叫 `customer_name`（客户姓名）。
        
        ### 第一步：原始数据
        
        ```
        column_info = {    "name": "customer_name",    "description": "客户姓名",    "alias": ["顾客名字", "用户姓名"]}
        ```
        
        ### 第二步：拆成4条数据
        
        你的代码会执行：
        
        ```
        一个字段：customer_name
               │
               ├── customer_name → UUID1
               ├── 客户姓名       → UUID2
               ├── 顾客名字       → UUID3
               └── 用户姓名       → UUID4
        ```
        
        为什么拆成4条？因为用户可能用这4种不同的说法来表达同一个字段。
        
        ### 第三步：把这4句话分别变成向量
        
        ```
        customer_name → [0.12, 0.33, ...] → UUID1
        客户姓名       → [0.21, 0.56, ...] → UUID2
        顾客名字       → [0.19, 0.51, ...] → UUID3
        用户姓名       → [0.23, 0.48, ...] → UUID4
        ```
        
        每个向量都是1024维。
        
        但是，这4条记录的 `payload` 都是：
        
        ```
        {    "name": "customer_name",    "description": "客户姓名",    "alias": ["顾客名字", "用户姓名"]}
        ```
        
        ### 第四步：存进 Qdrant
        
        | ID    | 向量来自哪段文字      | Payload 指向    |
        | ----- | ------------- | ------------- |
        | UUID1 | customer_name | customer_name |
        | UUID2 | 客户姓名          | customer_name |
        | UUID3 | 顾客名字          | customer_name |
        | UUID4 | 用户姓名          | customer_name |
        
        ### 第五步：用户真正来查询了
        
        用户问：
        
        “帮我查一下用户姓名。”
        
        ```
        用户输入："用户姓名"
               │
               ▼
        Embedding 模型
               │
               ▼
        生成查询向量
               │
               ▼
        Qdrant 相似度搜索
               │
               ▼
        命中 UUID4（用户姓名）
               │
               ▼
        读取 Payload
               │
               ▼
        找到真实数据库字段：
        customer_name
        ```
        
        这样大模型就知道，用户嘴里的“用户姓名”，对应数据库里的 `customer_name`。
        
        最关键的一句话：
        
        4种不同叫法 → 4个不同向量 → 4个不同ID → 但都指向同一个数据库字段。
        
        你这段代码做的就是提前建立这份“语义词典”，让后续的 NL2SQL 能听懂用户的不同表达。
    """

    async def _save_column_value_infos_to_es(self, column_infos: list[ColumnInfoMySQL], tables: list[TableConfig]):
        # 从tables中取出所有字段的sync值 dict[column_id,sync]
        column_sync_dict: dict[str, bool] = {}
        for table in tables:
            for column in table.columns:
                column_sync_dict[f'{table.name}.{column.name}'] = column.sync
        # 遍历column_infos中收集字段值信息列表
        value_infos: list[ValueInfoES] = []
        for column_info in column_infos:
            # 查询当前字段的所有值
            values: list = await self.dw_mysql_repository.get_column_values(column_info.table_id, column_info.name,
                                                                            limit=10000)
            # 如果当前字段是需要进行ES索引的
            if column_sync_dict.get(column_info.id):
                # 对每个字段值创建valueinfo对象添加到列表中
                for value in values:
                    value_infos.append(ValueInfoES(
                        id=f'{column_info.id}.{value}',
                        value=value,
                        type=column_info.type,
                        column_id=column_info.id,
                        column_name=column_info.name,
                        table_id=column_info.table_id,
                        table_name=column_info.table_id
                    ))
        # 将字段值信息列表保存到ES库中
        await self.value_es_repository.insert_value_infos(value_infos)

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
        # 遍历metrics_infos收集生成ids pyloads texts(name/description/alia)
        # 先收集生成一个list[dict(id/payload/text)]
        temp_list: list[dict] = []
        for metric_info in metrics_infos:
            payload = MetricInfoQdrant(
                id=metric_info.id,
                name=metric_info.name,
                description=metric_info.description,
                alias=metric_info.alias,
                relevant_columns=metric_info.relevant_columns
            )
            # name
            temp_list.append({
                'id': uuid.uuid4(),
                'text': metric_info.name,
                'payload': payload
            })

            # description
            temp_list.append({
                'id': uuid.uuid4(),
                'text': metric_info.description,
                'payload': payload
            })

            # alias中的每个alia
            for alia in metric_info.alias:
                temp_list.append({
                    'id': uuid.uuid4(),
                    'text': alia,
                    'payload': payload
                })

        ids: list[str] = [item['id'] for item in temp_list]
        payloads: list[str] = [item['payload'] for item in temp_list]
        texts: list[str] = [item['text'] for item in temp_list]
        # 对texts进行批量生成向量=>vectors
        batch_size = 16
        vectors: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_vectors: list[list[float]] = await self.embedding_client.aembed_documents(batch_texts)
            vectors.extend(batch_vectors)

        # 调用持久层保存字段信息列表ids payloads vectors
        await self.metric_qdrant_repository.insert_column_vectors(ids, payloads, vectors)
