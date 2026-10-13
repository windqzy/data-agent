# 创建对应对象
import uuid

import uvicorn
from fastapi import FastAPI, Request

from app.api.routers.query_router import query_router
from app.core.context import set_req_id
from app.core.lifespan import lifespan

# 创建应用对象
app = FastAPI(lifespan=lifespan)
# 注册路由
app.include_router(query_router)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    # 在处理请求前生辰一个唯一的id并保存
    set_req_id(uuid.uuid4())
    return await call_next(request)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
