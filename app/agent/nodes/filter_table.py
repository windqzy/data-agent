from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def filter_table(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer('过滤表和字段')
    # 过滤表和字段处理
    try:
        return {}
    except Exception as e:
        logger.error(f'过滤表和字段失败：str(e)')
        raise
