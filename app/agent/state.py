from typing import TypedDict

from app.models.es.value_info_es import ValueInfoES
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant


# 当前日期时间的状态信息
class DateInfoState(TypedDict):
    date: str # 年月日
    weekday: str # 星期
    quarter: str # 季度  Q1-Q4

# 数据库信息
class DBInfoState(TypedDict):
    version: str # 版本号
    dialect: str # 数据库名称


class ColumnInfoState(TypedDict):
    name: str
    type: str
    role: str
    examples: list
    description: str
    alias: list


class TableInfoState(TypedDict):
    name: str
    role: str
    description: str
    columns: list[ColumnInfoState]


class MetricInfoState(TypedDict):
    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]


class DataAgentState(TypedDict):
    query: str  # 用户提问
    keywords: list[str]  # 关键词列表
    sql: str  # 生成的sql
    error: str  # sql校验的错误信息
    recall_columns: list[ColumnInfoQdrant]  # 召回的字段信息列表
    recall_metrics: list[MetricInfoQdrant]  # # 召回的指标信息列表
    recall_metrics: list[MetricInfoQdrant]  # # 召回的指标信息列表
    recall_values: list[ValueInfoES]  # # 召回的指标信息列表
    table_infos: list[TableInfoState]  # 带字段信息列表的表信息列表
    metric_infos: list[MetricInfoState]  # 指标信息列表
    date_info: DateInfoState #当前日期
    db_info: DBInfoState #数据库的信息
