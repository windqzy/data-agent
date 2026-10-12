import asyncio
from typing import TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.runtime import Runtime

from app.repositories.es.value_es_repository import ValueESRepository


class MyState(TypedDict):
    query: str
    keywords: list[str]
    sql: str
    error: str


# 在多个节点函数间传递一些不变数据/依赖对象 怎么操作
# 自定义context类型
class MyContext(TypedDict):
    db_name: str
    value_es_repo: ValueESRepository


# 定义节点
def extract_keywords(state: MyState, runtime: Runtime[MyContext], config: RunnableConfig):
    print(runtime)
    print(config)
    db_name = runtime.context['db_name']
    print(f'db_name==={db_name}')
    # 向调用输出自定义数据
    runtime.stream_writer('抽取关键字')
    query = state['query']
    print(f'抽取关键词：query={query}')
    keywords = ['你', '是', '谁']
    # 返回状态关心（注意：不要直接更新状态）
    return {'keywords': keywords}  # langgraph会自动将状态更新合并到state中，并传递给下一个节点


def generate_sql(state: MyState, runtime: Runtime):
    # 向调用输出自定义数据
    runtime.stream_writer('生成sql')
    query = state['query']
    keywords = state['keywords']
    print(f'生成sql query={query},keywords={keywords}')
    return {
        'sql': 'select * from table_name'
    }


# 创建状态图
state_graph = StateGraph(state_schema=MyState,  # 指定自定义的状态类型
                         context=MyContext)  # 指定自定义的Context类型
# 添加节点
state_graph.add_node("extract_keywords", extract_keywords)
state_graph.add_node("generate_sql", generate_sql)

# 添加边
state_graph.add_edge(START, "extract_keywords")
state_graph.add_edge("extract_keywords", "generate_sql")
state_graph.add_edge("generate_sql", END)

# 编译状态图
compiled_graph = state_graph.compile()

# 执行(异步流式执行)
if __name__ == '__main__':
    async def test():
        # 创建初始的状态对象
        state = MyState(query="你是谁？")

        # 创建上下文对象
        context = MyContext(db_name="dw2")
        # stream_mode='updates' :得到每个节点返回的状态更新 增量
        # stream_mode='values'  :合并后的状态 state
        # stream_mode='custom'  :得到自定义输出 配合runtime使用
        async for chunk in compiled_graph.astream(input=state,
                                                  context=context,
                                                  stream_mode='custom',
                                                  config={'thread_id': 'abc'}):
            print('----', chunk)  # 各个节点返回的状态更新


    asyncio.run(test())


#1.创建状态图 指定state类型 和 context类型
#2.添加节点 节点就是自定义的函数，处理特定逻辑
#3.添加边 方便state传递
#4.编译图
