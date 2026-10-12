from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def validate_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer('校验sql')
    # 校验sql处理
    try:
        sql = state['sql']
        dw_mysql_repository = runtime.context['dw_mysql_repository']
        await dw_mysql_repository.validate_sql(sql)
        logger.info("校验SQL完成")
        return {'error': None}  # 会自动进行执行sql节点
    except Exception as e:
        logger.error(f'校验sql失败：str(e)')
        return {'error': f'校验sql失败：{str(e)}'}  # 会自动进行校正节点
