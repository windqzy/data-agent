from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.nodes.correct_sql import MAX_FAIL_COUNT
from app.agent.state import DataAgentState
from app.core.log import logger


async def validate_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer({'stage':'校验sql'})
    # 检查是否已经达到最大失败次数
    fail_count = state['fail_count']
    # 校验sql处理
    try:
        if fail_count == MAX_FAIL_COUNT:
            raise Exception("已经达到sql校正的最大次数")
        sql = state['sql']
        dw_mysql_repository = runtime.context['dw_mysql_repository']
        await dw_mysql_repository.validate_sql(sql)

        # 模拟SQL校验失败
        raise Exception("SQL语法可能有问题")

        logger.info("校验SQL完成")
        return {'error': None}  # 会自动进行执行sql节点
    except Exception as e:
        if fail_count == MAX_FAIL_COUNT:
            raise e
        logger.error(f'校验sql失败：str(e)')
        return {'error': f'校验sql失败：{str(e)}'}  # 会自动进行校正节点
