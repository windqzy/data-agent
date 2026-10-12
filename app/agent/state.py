from typing import TypedDict


class DataAgentState(TypedDict):
    query: str  # 用户提问
    keywords: list[str]  # 关键词列表
    sql: str  # 生成的sql
    error: str  # sql校验的错误信息

