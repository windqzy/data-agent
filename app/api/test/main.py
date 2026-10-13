import asyncio

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from app.api.test.order_router import order_router
from app.api.test.product_router import product_router

# 创建应用对象
app = FastAPI()

#技术点4:SSE流式响应
async def fake_stream():
    for i in range(10):
        yield f'data: {{"data":"abc{i}"}} \n\n'
        await asyncio.sleep(1)

async def call_async_generator():
    #等待下一条数据，拿到后执行循环体，直到没有数据为止。
    async for chunk in fake_stream():
        print('----',chunk)
"""
async def	这个函数允许执行异步操作
for	从普通可迭代对象中逐个取数据
async for	从异步可迭代对象中等待并获取数据
"""
@app.get("/sse")
def test_sse():
    print("处理对/sse的GET请求")
    return StreamingResponse(fake_stream(), media_type="text/event-stream")

#技术点3:使用路由器
#假设当前项目有2个模块：product模块(5) order模块(6)
#定义一个模块包含product模块所有接口路由  需要路由器
#定义一个模块包含order模块所有接口路由 需要路由器
#需要注册路由器才能使用路由器
app.include_router(product_router,prefix="/v1")
app.include_router(order_router,prefix="/v2")

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
    # uvicorn.run(app, host='127.0.0.1', port=6789)
    asyncio.run(call_async_generator())
