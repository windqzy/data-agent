from typing import TypedDict

from app.models.es.value_info_es import ValueInfoES
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant


class DataAgentState(TypedDict):
    query: str  # 用户提问
    keywords: list[str]  # 关键词列表
    sql: str  # 生成的sql
    error: str  # sql校验的错误信息
    recall_columns: list[ColumnInfoQdrant]  # 召回的字段信息列表
    recall_metrics: list[MetricInfoQdrant]  # # 召回的指标信息列表
    recall_metrics: list[MetricInfoQdrant]  # # 召回的指标信息列表
    recall_values: list[ValueInfoES]  # # 召回的指标信息列表
