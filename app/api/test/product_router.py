# 定义一个模块包含product模块所有接口路由  需要路由器
from fastapi import APIRouter

product_router = APIRouter()


# 通过当前路由器来定义当前模块的所有路由
@product_router.get("/product/{id}")
def test_get(id: int):
    print("处理对/product的GET球球}")
    return {"id": id,
            "name": 'product的名称'
            }

#还可以定义很多其他路由