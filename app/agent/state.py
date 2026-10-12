from typing import TypedDict

from app.models.es.value_info_es import ValueInfoES
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant


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
