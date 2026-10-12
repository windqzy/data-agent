from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

"""
用来操作Mysql数据库中的dw库的持久层模块
"""


class DWMysqlRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    """
    show columns from dim_customer
    
    Field          Type
    customer_id	    varchar(20)	NO	PRI		
    customer_name	varchar(50)	YES			
    gender	        varchar(10)	YES			
    member_level	varchar(20)	YES			
    """

    async def get_column_types(self, table_name: str) -> dict[str, str]:
        sql = f"show columns from {table_name}"
        result = await self.session.execute(text(sql))
        return {
            row.Field: row.Type for row in result.all()
        }

    """
    select distinct customer_name from dim_customer limit 10
    """

    async def get_column_values(self, table_name: str, column_name: str, limit: int = 10) -> list[Any]:
        sql = f"select distinct {column_name} from {table_name} limit {limit}"
        result = await self.session.execute(text(sql))
        return result.scalars().all()

    # 获取数据库的名称和版本
    async def get_db_info(self) -> dict[str,str]:
        sql = 'select version()'
        result = await self.session.execute(text(sql))
        version:str = result.scalar()
        dialect = self.session.bind.dialect.name
        return {
            'version': version,
            'dialect': dialect
        }

    #检查sql是否语法正确
    async def validate_sql(self, sql: str):
        await self.session.execute(text(f'explain {sql}'))

