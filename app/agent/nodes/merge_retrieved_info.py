from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState, TableInfoState, ColumnInfoState, MetricInfoState
from app.core.log import logger
from app.models.mysql.column_info_mysql import ColumnInfoMySQL
from app.models.mysql.table_info_mysql import TableInfoMySQL
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant


def _convert_column_info_mysql_to_qdrant(column_info_mysql: ColumnInfoMySQL) -> ColumnInfoQdrant:
    return ColumnInfoQdrant(
        id=column_info_mysql.id,
        name=column_info_mysql.name,
        description=column_info_mysql.description,
        role=column_info_mysql.role,
        type=column_info_mysql.type,
        examples=column_info_mysql.examples,
        table_id=column_info_mysql.table_id,
        alias=column_info_mysql.alias
    )


def _convert_column_info_qdrant_to_state(column: ColumnInfoQdrant) -> ColumnInfoState:
    return ColumnInfoState(
        name=column['name'],
        type=column['type'],
        role=column["role"],
        examples=column["examples"],
        description=column["description"],
        alias=column["alias"]
    )

def _convert_metric_info_qdrant_to_state(recall_metric:MetricInfoQdrant):
    return MetricInfoState(
        name=recall_metric['name'],
        description=recall_metric["description"],
        relevant_columns=recall_metric["relevant_columns"],
        alias=recall_metric["alias"]
    )


async def merge_retrieved_info(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer('合并召回')
    # 合并召回处理
    try:
        recall_columns = state['recall_columns']
        recall_metrics = state['recall_metrics']
        recall_values = state['recall_values']
        meta_mysql_repository = runtime.context['meta_mysql_repository']
        # 1.收集一个最完整的字段信息列表 去重合并 dict[column_id,ColumnInfoQdrant]
        # 1.1 收集召回的指标信息列表
        column_infos_dict: dict[str, ColumnInfoQdrant] = {item['id']: item for item in recall_columns}
        # 1.2 继续收集召回的指标信息列表的字段信息列表
        for metric in recall_metrics:
            for column_id in metric['relevant_columns']:
                # 查询column_id对应的字段信息
                column_info_mysql: ColumnInfoMySQL = await meta_mysql_repository.get_column_info_by_id(column_id)
                column_infos_dict[column_id] = _convert_column_info_mysql_to_qdrant(column_info_mysql)
        # 1.3 继续收集字段值信息列表对应的字段信息列表 将字段值保存到字段的值的样例列表中
        for recall_value in recall_values:
            column_id = recall_value['column_id']
            # 查询column_id对应的字段信息
            column_info_mysql: ColumnInfoMySQL = await meta_mysql_repository.get_column_info_by_id(column_id)
            column_infos_dict[column_info_mysql.id] = _convert_column_info_mysql_to_qdrant(column_info_mysql)

        # 2. 根据收集的所有字段信息列表 生成带字段信息列表的表信息列表
        # 2.1 对收集的字段信息列表进行按表id进行分组：dict[table_id,list[ColumnInfoQdrant]]
        table_column_info_dict: dict[str, list[ColumnInfoQdrant]] = {}
        for column_info in column_infos_dict.values():
            table_id = column_info['table_id']
            if table_id not in table_column_info_dict:
                table_column_info_dict[table_id] = []
            table_column_info_dict[table_id].append(column_info)

        # 2.2 生成带字段信息列表的表信息列表 table_infos:list[TableInfoState]
        table_infos: list[TableInfoState] = []
        for table_id, column_infos in table_column_info_dict.items():
            # 1.4 最后收集表的主键和外键对应的字段信息列表
            # 查询当前表的主键和外键字段信息列表
            key_column_infos: list[ColumnInfoMySQL] = await meta_mysql_repository.get_key_column_infos(table_id)
            for key_column_info in key_column_infos:
                # 当前字段id没有在前面搜集的字段信息列表中 我才去添加
                if key_column_info.id not in column_infos_dict:
                    table_column_info_dict[table_id].append(_convert_column_info_mysql_to_qdrant(key_column_info))
            # 根据表id查询meta得到表信息
            table_info_mysql: TableInfoMySQL = await meta_mysql_repository.get_table_info_by_id(table_id)
            columns: list[ColumnInfoState] = [
                _convert_column_info_qdrant_to_state(item)
                for item in column_infos]
            # 创建带字段信息列表的表信息对象，并添加到列表中
            table_infos.append(TableInfoState(
                name=table_info_mysql.name,
                role=table_info_mysql.role,
                description=table_info_mysql.description,
                columns=columns
            ))
        #整理召回的指标信息列表
        metric_infos:list[MetricInfoState] = [
            _convert_metric_info_qdrant_to_state(metric)
            for metric in recall_metrics
        ]
        logger.info(f'合并召回完成：table_infos={table_infos}')
        logger.info(f'合并召回完成：metric_infos={metric_infos}')
        return {
            'table_infos': table_infos,
            'metric_infos': metric_infos,
        }
    except Exception as e:
        logger.error(f'合并召回失败：str(e)')
        raise


"""
recall_columns ──┐
recall_metrics ──┼──► 合并字段 → 去重 → 按表分组
recall_values ───┘                    │
                                     ▼
                            table_infos（表结构）
                            metric_infos（指标信息）
                                     │
                                     ▼
                              generate_sql
"""