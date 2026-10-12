from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def filter_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer('过滤指标')
    # 过滤指标处理
    try:
        return {}
    except Exception as e:
        logger.error(f'过滤指标失败：str(e)')
        raise
