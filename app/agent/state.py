from typing import TypedDict

from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant


class DataAgentState(TypedDict):
    query: str  # 用户提问
    keywords: list[str]  # 关键词列表
    sql: str  # 生成的sql
    error: str  # sql校验的错误信息
    recall_columns: list[ColumnInfoQdrant]  # 召回的字段信息列表
