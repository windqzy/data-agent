from fastapi import APIRouter, Depends
from starlette.responses import StreamingResponse

from app.api.dependencies import get_query_servive
from app.api.schemas.query_schema import QuerySchema
from app.services.query_service import QueryService

# 创建路由器
query_router = APIRouter()

# 注册路由
@query_router.post("/api/query")
def query(query_schema: QuerySchema,
          query_service:QueryService=Depends(get_query_servive)):
    return StreamingResponse(query_service.search(query_schema.query),
                             media_type="text/event-stream")
