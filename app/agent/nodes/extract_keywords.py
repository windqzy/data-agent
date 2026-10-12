from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def extract_keywords(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer('提取关键词')
    # 提取关键词处理
    try:
        return {}
    except Exception as e:
        logger.error(f'提取关键词失败：str(e)')
        raise
