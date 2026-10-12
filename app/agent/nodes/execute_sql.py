from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def execute_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer('执行sql')
    # 执行sql处理
    try:
        return {}
    except Exception as e:
        logger.error(f'执行sql失败：str(e)')
        raise
