import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt

"""
1.利用大模型对指标信息进行过滤，生成需要指标
2.对metric_infos中多余的表和字段信息
3.返回处理后的metric_infos
"""


async def filter_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer('过滤指标')
    # 过滤指标处理
    try:
        query = state['query']
        metric_infos = state['metric_infos']

        # 1.利用大模型对提问进行必要的字段整理
        prompt_template: str = PromptTemplate(
            template=load_prompt('filter_metric_info'),
            input_variables=['query', 'metric_infos'],
        )
        output_parser = JsonOutputParser()
        chain = prompt_template | llm | output_parser
        # 给prompt用的
        result = chain.invoke({'query': query,
                               'metric_infos': yaml.dump(metric_infos, allow_unicode=True, sort_keys=False)})
        """
        [
          "指标名1",
          "指标名2"
        ]
        """
        # 2.过滤掉table_infos中多余的表和字段信息
        # 注意：不能在遍历的同时做删除
        # 遍历浅拷贝的数组，删除的是原数组
        for metric_info in metric_infos[:]:
            metric_name = metric_info['name']  # 过滤表信息
            if metric_name not in result:
                metric_infos.remove(metric_info)
        logger.info(f'过滤指标完成：{metric_infos}')
        return {
            'metric_infos': metric_infos
        }
    except Exception as e:
        logger.error(f'过滤指标失败：str(e)')
        raise
