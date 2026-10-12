from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def recall_value(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer('召回字段值')
    # 召回字段值处理
    try:
        return {}
    except Exception as e:
        logger.error(f'召回字段值失败：str(e)')
        raise
