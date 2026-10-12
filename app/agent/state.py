from typing import TypedDict


class DataAgentState(TypedDict):
    query: str
    keywords: list[str]
    sql: str
    error: str


