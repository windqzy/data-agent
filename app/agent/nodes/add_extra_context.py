from datetime import datetime

from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState, DateInfoState, DBInfoState
from app.core.log import logger



async def add_extra_context(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer('添加额外信息')
    # 添加额外信息处理
    try:
        dw_mysql_repository = runtime.context['dw_mysql_repository']
        #得到日期信息
        today = datetime.today()
        date = today.strftime("%Y-%m-%d")
        weekday = today.strftime("%A")
        quarter = f'Q{(today.month+2)//3}'
        date_info = DateInfoState(
            date=date,
            weekday=weekday,
            quarter=quarter
        )
        #得到数据库信息
        db_info_dict:dict[str,str] = await dw_mysql_repository.get_db_info()
        db_info:DBInfoState = DBInfoState(**db_info_dict)
        logger.info(f'添加额外信息完成：date_info:{date_info} ---db_info:{db_info} ')
        #返回
        return {
            'date_info': date_info,
            'db_info': db_info
        }
    except Exception as e:
        logger.error(f'添加额外信息失败：str(e)')
        raise
