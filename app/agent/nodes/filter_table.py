import yaml
from dns.e164 import query
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt

"""
1.利用大模型对表和字段信息进行过滤，生成需要的表名和字段名
2.对table_infos中多余的表和字段信息
3.返回处理后的table_infos
"""


async def filter_table(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer('过滤表和字段')
    # 过滤表和字段处理
    try:
        query = state['query']
        table_infos = state['table_infos']

        column_qdrant_repository = runtime.context['column_qdrant_repository']
        embedding_client = runtime.context['embedding_client']
        # 1.利用大模型对提问进行必要的字段整理
        prompt_template: str = PromptTemplate(
            template=load_prompt('filter_table_info'),
            input_variables=['query', 'table_infos'],
        )
        output_parser = JsonOutputParser()
        chain = prompt_template | llm | output_parser
        # 给prompt用的
        result = chain.invoke({'query': query,
                               'table_infos': yaml.dump(table_infos, allow_unicode=True, sort_keys=False)})
        """
        {
            "表名1":["字段1", "字段2", "..."],
            "表名2":["字段1", "字段2", "..."]
        }
        """
        # 2.过滤掉table_infos中多余的表和字段信息
        # 注意：不能在遍历的同时做删除
        # 遍历浅拷贝的数组，删除的是原数组
        for table_info in table_infos[:]:
            table_name = table_info['name']  # 过滤表信息
            if table_name not in result:
                table_infos.remove(table_info)
            else:
                for column in table_info['columns'][:]:
                    column_name = column['name']
                    column_names = result[table_name]
                    if column_name not in column_names:
                        table_info['columns'].remove(column)  # 过滤字段信息
        logger.info(f'过滤表和字段完成：{table_infos}')
        return {
            'table_infos': table_infos
        }
    except Exception as e:
        logger.error(f'过滤表和字段失败：str(e)')
        raise


"""
遍历的副本 b = a[:]       被修改的原列表 a

下标 0 → A ────────────► A
下标 1 → B ────────────► B
下标 2 → C ────────────► C
下标 3 → D ────────────► D

遍历 b 的 A → 删除 a 的 A

副本 b                     原列表 a
[A, B, C, D]               [B, C, D]
    ↑
下一次继续遍历 B

遍历 b 的 B → 删除 a 的 B

副本 b                     原列表 a
[A, B, C, D]               [C, D]
       ↑
继续遍历 C
"""
