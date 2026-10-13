from typing import Any

from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def execute_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer({'stage':'执行sql'})
    # 执行sql处理
    try:
        sql = state['sql']
        dw_mysql_repository = runtime.context['dw_mysql_repository']
        result: list[Any] = await dw_mysql_repository.execute_sql(sql)
        # 输出结果数据给调用者
        runtime.stream_writer({'result': result})
    except Exception as e:
        logger.error(f'执行sql失败：str(e)')
        raise
