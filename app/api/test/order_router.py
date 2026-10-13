#定义一个模块包含order模块所有接口路由 需要路由器

from fastapi import APIRouter

order_router = APIRouter()


# 通过当前路由器来定义当前模块的所有路由
@order_router.get("/order/{id}")
def test_get(id: int):
    print("处理对/order的GET球球}")
    return {"id": id,
            "name": 'order的名称'
            }

#还可以定义很多其他路由