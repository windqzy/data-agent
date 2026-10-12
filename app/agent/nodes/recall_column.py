from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.prompt.prompt_loader import load_prompt

"""
1.利用大模型对提问进行语义化提取关键词，与结巴提取的关键词进行去重合并，生成一个完整的关键词列表
2.将keywords批量向量化 keyword_vectors list[list[float]]
3.遍历每个keyword_vector 去Qdrant查询匹配的字段信息列表,并进行去重合并=》list[ColumnInfoQdrant]
4.返回召回的字段信息列表 recall_columns
"""


async def recall_column(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer('召回字段')
    # 召回字段处理
    try:
        query = state['query']
        keywords = state['keywords']
        column_qdrant_repository = runtime.context['column_qdrant_repository']
        embedding_client = runtime.context['embedding_client']
        # 1.利用大模型对提问进行语义化提取关键词，与结巴提取的关键词进行去重合并，生成一个完整的关键词列表
        prompt_template: str = PromptTemplate(
            template=load_prompt('extend_keywords_for_column_recall'),
            input_variables=['query']
        )
        output_parser = JsonOutputParser()
        chain = prompt_template | llm | output_parser
        result = chain.invoke({'query': query})
        logger.info(f'recall_column llm keywords={result}')
        keywords = list(set(keywords + result))
        # 2.将keywords批量向量化 keyword_vectors list[list[float]]
        keyword_vectors: list[list[float]] = await embedding_client.aembed_documents(keywords)
        # 3.遍历每个keyword_vector 去Qdrant查询匹配的字段信息列表,并进行去重合并=》list[ColumnInfoQdrant]
        column_infos_dict: dict[str, ColumnInfoQdrant] = {}
        for keyword_vector in keyword_vectors:
            column_infos: list[ColumnInfoQdrant] = await column_qdrant_repository.search(keyword_vector)
            for column_info in column_infos:
                column_id = column_info['id']
                if column_id not in column_infos_dict:
                    column_infos_dict[column_id] = column_info
        # 4.返回召回的字段信息列表 recall_columns
        recall_columns: list[ColumnInfoQdrant] = list(column_infos_dict.values())
        logger.info(f'召回字段完成：{recall_columns}')
        return {
            'recall_columns': recall_columns
        }
    except Exception as e:
        logger.error(f'召回字段失败：str(e)')
        raise
