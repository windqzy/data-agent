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
1.利用大模型对表和字段信息进行过滤，生成需要的表名和字段名
2.对table_infos中多余的表和字段信息
3.返回处理后的table_infos
"""


async def filter_table(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer({'stage':'过滤表和字段'})
    # 过滤表和字段处理
    try:
        query = state['query']
        table_infos = state['table_infos']
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
拷贝的容器存储的是同一批对象的引用（地址），迭代器遍历的是新容器中的位置。
看这个内存结构：
code
Code
原列表 A                      浅拷贝列表 B
地址：0x100                   地址：0x200

下标0 → 地址0xA ──┐     下标0 → 地址0xA ──┐
下标1 → 地址0xB ──┤     下标1 → 地址0xB ──┤
下标2 → 地址0xC ──┤     下标2 → 地址0xC ──┤
                  │                       │
                  ▼                       ▼
             共享同一批对象
                A、B、C
假设执行：
code
Code
for item in a[:]:    a.remove(item)
实际过程：
code
Code
① 迭代器读取副本下标0 → 对象A
   原列表删除A → [B, C]
   副本不变   → [A, B, C]

② 迭代器读取副本下标1 → 对象B
   原列表删除B → [C]
   副本不变   → [A, B, C]

③ 迭代器读取副本下标2 → 对象C
   原列表删除C → []
所以关键是：
迭代器按照副本的下标依次取出对象引用，而删除操作改变的是原列表中的引用排列。
对象本身没有因为 remove() 被移动到另一个内存地址；移动的是原列表中保存引用的位置。
你可以记成：
浅拷贝 = 新容器 + 旧对象引用。
"""
