from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def merge_retrieved_info(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer('合并召回')
    # 合并召回处理
    try:
        return {}
    except Exception as e:
        logger.error(f'合并召回失败：str(e)')
        raise
