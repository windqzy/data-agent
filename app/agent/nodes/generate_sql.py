import yaml
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt


async def generate_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer('生成sql')
    # 生成sql处理
    try:
        query = state['query']
        table_infos = state['table_infos']
        metric_infos = state['metric_infos']
        date_info = state['date_info']
        db_info = state['db_info']

        # 1.利用大模型对提问进行必要的字段整理
        prompt_template: str = PromptTemplate(
            template=load_prompt('generate_sql'),
            input_variables=['query', 'table_infos', 'metric_infos', 'date_info', 'db_info'],
        )
        output_parser = StrOutputParser()
        chain = prompt_template | llm | output_parser
        # 给prompt用的
        sql = chain.invoke({'query': query,
                            'table_infos': yaml.dump(table_infos, allow_unicode=True, sort_keys=False),
                            'metric_infos': yaml.dump(metric_infos, allow_unicode=True, sort_keys=False),
                            'date_info': yaml.dump(date_info, allow_unicode=True, sort_keys=False),
                            'db_info': yaml.dump(db_info, allow_unicode=True, sort_keys=False)})
        logger.info(f'生成sql完成：{sql}')

        return {
            'sql': sql
        }
    except Exception as e:
        logger.error(f'生成sql失败：str(e)')
        raise
