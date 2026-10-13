from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.models.es.value_info_es import ValueInfoES
from app.prompt.prompt_loader import load_prompt

"""
1.利用大模型对提问进行语义化提取关键词，与结巴提取的关键词进行去重合并，生成一个完整的关键词列表
2.遍历每个keyword 去ES查询匹配的字段值信息列表,并进行去重合并=》recall_values list[ValueInfoES]
3.返回召回的字段值信息列表 recall_values
"""


async def recall_value(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer({'stage':'召回字段值'})
    # 召回字段处理
    try:
        query = state['query']
        keywords = state['keywords']
        value_es_repository = runtime.context['value_es_repository']
        # 1.利用大模型对提问进行语义化提取关键词，与结巴提取的关键词进行去重合并，生成一个完整的关键词列表
        prompt_template: str = PromptTemplate(
            template=load_prompt('extend_keywords_for_metric_recall'),
            input_variables=['query']
        )
        output_parser = JsonOutputParser()
        chain = prompt_template | llm | output_parser
        result = chain.invoke({'query': query})
        logger.info(f'recall_metric llm keywords={result}')
        keywords = list(set(keywords + result))
        # 2.遍历每个keyword_vector 去Qdrant查询匹配的字段信息列表,并进行去重合并=》list[MetricInfoQdrant]
        value_infos_dict: dict[str, ValueInfoES] = {}
        for keyword in keywords:
            value_infos: list[ValueInfoES] = await value_es_repository.search(keyword)
            for value_info in value_infos:
                value_id = value_info['id']
                if value_id not in value_infos_dict:
                    value_infos_dict[value_id] = value_info
        # 4.返回召回的字段信息列表 recall_metrics
        recall_values: list[ValueInfoES] = list(value_infos_dict.values())
        logger.info(f'召回字段值完成：{recall_values}')
        return {
            'recall_values': recall_values
        }
    except Exception as e:
        logger.error(f'召回字段值失败：str(e)')
        raise
