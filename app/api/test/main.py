import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, Depends
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from app.api.test.order_router import order_router
from app.api.test.product_router import product_router
from app.clients.es_client_manager import es_client_manager
from app.models.es.value_info_es import ValueInfoES
from app.repositories.es.value_es_repository import ValueESRepository


# 技术点5：生命周期
@asynccontextmanager
async def lifespan(spp):
    print("在应用启动时执行一次，一般执行一次行的初始化处理，比如：初始化客户端")
    es_client_manager.init_client()
    yield
    print("在应用结束时执行一次，一般执行收尾的处理，比如：关闭客户端")
    es_client_manager.close_client()


# 创建FastAPI的应用对象
app = FastAPI(lifespan=lifespan)


# 技术点7:依赖注入（自动注入）
# 功能：根据传入的keyword参数去es中出啊训对应的字段值信息列表
# 依赖对象：value_es_repository
# 路由函数依赖的对象通过形参自动注入进来value_es_repository: ValueESRepository = Depends(get_value_es_repository)
# 同时要提供这个对象创建的函数


# 返回依赖对象的回调函数
# 每次路由函数处理请求前由FastAPI执行
def get_value_es_repository():
    print("get_value_es_repository()")
    return ValueESRepository(es_client_manager.client)


@app.get('/di')
async def test_di(keyword: str, value_es_repository: ValueESRepository = Depends(get_value_es_repository)):
    print('处理对/di的get请求')
    value_infos: list[ValueInfoES] = await value_es_repository.search(keyword)
    return value_infos


# 技术点6：请求中间件
@app.middleware('http')
async def middleware_func(request: Request, call_next):
    print("处理请求前执行")
    response = await call_next(request)  # 调用目标路由的处理请求
    print("处理请求后执行")
    return response


# 技术点4:SSE流式响应
async def fake_stream():
    for i in range(10):
        yield f'data: {{"data":"abc{i}"}} \n\n'
        await asyncio.sleep(1)


async def call_async_generator():
    # 等待下一条数据，拿到后执行循环体，直到没有数据为止。
    async for chunk in fake_stream():
        print('----', chunk)


"""
async def	这个函数允许执行异步操作
for	从普通可迭代对象中逐个取数据
async for	从异步可迭代对象中等待并获取数据
"""


@app.get("/sse")
def test_sse():
    print("处理对/sse的GET请求")
    return StreamingResponse(fake_stream(), media_type="text/event-stream")


# 技术点3:使用路由器
# 假设当前项目有2个模块：product模块(5) order模块(6)
# 定义一个模块包含product模块所有接口路由  需要路由器
# 定义一个模块包含order模块所有接口路由 需要路由器
# 需要注册路由器才能使用路由器
app.include_router(product_router, prefix="/v1")
app.include_router(order_router, prefix="/v2")


# 技术点1:处理不同类型的请求
@app.get("/xxx")
def test_get():
    print("处理对/xxxx的GET请求")
    return {"message": "处理对/xxxx的GET请求的结果数据 "}


@app.post("/xxx")
def test_post():
    print("处理对/xxxx的POST请求")
    return {"message": "处理对/xxxx的POST请求的结果数据 "}


class BodyParams(BaseModel):
    name: str
    age: int


# 技术点2:获取不同类型的参数 请求体参数 路径参数 query参数
@app.post('/params/{id}')
def test_params(body_params: BodyParams, id: int, sex: str):
    print('处理对/params的POST请求', id, body_params.name, body_params.age, sex)
    return {
        'id': id,
        'name': body_params.name,
        'age': body_params.age,
        'sex': sex
    }


# 运行应用
if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=6789)
    # asyncio.run(call_async_generator())
