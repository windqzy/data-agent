from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant
from app.prompt.prompt_loader import load_prompt

"""
1.利用大模型对提问进行语义化提取关键词，与结巴提取的关键词进行去重合并，生成一个完整的关键词列表
2.将keywords批量向量化 keyword_vectors list[list[float]]
3.遍历每个keyword_vector 去Qdrant查询匹配的字段信息列表,并进行去重合并=》list[MetricInfoQdrant]
4.返回召回的字段信息列表 recall_metrics
"""


async def recall_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer('召回指标')
    # 召回字段处理
    try:
        query = state['query']
        keywords = state['keywords']
        metric_qdrant_repository = runtime.context['metric_qdrant_repository']
        embedding_client = runtime.context['embedding_client']
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
        # 2.将keywords批量向量化 keyword_vectors list[list[float]]
        keyword_vectors: list[list[float]] = await embedding_client.aembed_documents(keywords)
        # 3.遍历每个keyword_vector 去Qdrant查询匹配的字段信息列表,并进行去重合并=》list[MetricInfoQdrant]
        metric_infos_dict: dict[str, MetricInfoQdrant] = {}
        for keyword_vector in keyword_vectors:
            metric_infos: list[MetricInfoQdrant] = await metric_qdrant_repository.search(keyword_vector)
            for metric_info in metric_infos:
                metric_id = metric_info['id']
                if metric_id not in metric_infos_dict:
                    metric_infos_dict[metric_id] = metric_info
        # 4.返回召回的字段信息列表 recall_metrics
        recall_metrics: list[MetricInfoQdrant] = list(metric_infos_dict.values())
        logger.info(f'召回指标完成：{recall_metrics}')
        return {
            'recall_metrics': recall_metrics
        }
    except Exception as e:
        logger.error(f'召回指标失败：str(e)')
        raise
