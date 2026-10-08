import asyncio
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.conf.app_config import DBConfig, app_config


class MysqlClientManager:
    def __init__(self, config: DBConfig):
        self.config = config
        # self.client:AsyncEngine|None = None
        self.client: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None

    def get_url(self) -> str:
        return (f'mysql+asyncmy://{self.config.user}:'
                f'{self.config.password}@{self.config.host}:'
                f'{self.config.port}'
                f'/{self.config.database}?charset=utf8mb4')

    def init_client(self, config: DBConfig):
        self.client = create_async_engine(self.get_url(),
                                          pool_size=10,  # 常驻连接的个数，默认是5
                                          max_overflow=10  # 临时创建的最大连接数
                                          # 初始化直接创建10个常驻连接，获取时直接返回
                                          # 当常驻连接用满了，创建临时连接
                                          # 当临时连接数达到最大值时，等待
                                          # 在等待的最大时间内，如果有常驻连接返回或临时链接释放
                                          # 一旦超过了最大等待时间，报错
                                          )

        self.session_factory = async_sessionmaker(bind=self.client,
                                            autoflush=True,
                                            # 自动刷新未提交的的更新到暂存区
                                            # 后查询会看到未提交(事务)的数据
                                            autobegin=True  # 自动开启事务，需要手动提交或者回滚事务
                                            )


    async def close_client(self):
        await self.client.dispose()


# 创建针对dw的客户端管理器
dw_mysql_client_manager = MysqlClientManager(app_config.db_dw)
# 创建针对meta的客户端管理器
meta_mysql_client_manager = MysqlClientManager(app_config.db_meta)

if __name__ == '__main__':
    # 测试查询dw库中的dim_customer表中的数据
    async def test():
        # 初始化客户端
        dw_mysql_client_manager.init_client(app_config.db_dw)
        # 利用客户端查询数据表数据
        # 创建一个会话对象
        async with AsyncSession(bind=dw_mysql_client_manager.client,
                                autoflush=True,
                                # 自动刷新未提交的的更新到暂存区
                                # 后查询会看到未提交(事务)的数据
                                autobegin=True  # 自动开启事务，需要手动提交或者回滚事务
                                ) as session:
            # 执行查询SQL
            # sql = 'select * from dim_customer limit 2'
            sql = 'select customer_name from dim_customer limit 2'
            result = await session.execute(text(sql))
            # 读取数据
            """
                result.all() 返回[row,row] 
                Row对象是包含当前行的字段值的可遍历的对象
                result.mappings().all() 返回[rowMapping,rowMapping] 
                Row对象是包含当前行的字段名和字段值的可遍历的对象
                result.scalars().all() 返回[val,val] 
                val是查询的第一列的字段值
            """
            # rows:list[Row] = result.all()
            # # print(rows,type(rows[0]))
            # for row in rows:
            #     for val in row:
            #         print(val)
            # print(rows[0].customer_name)

            # rows = result.mappings().all()
            # print(rows,type(rows[0]))
            # for row in rows:
            #     for key,val in row.items():
            #         print(key,val)
            # print(rows[0]['customer_name'])

            rows = result.scalars().all()
            print(rows, type(rows[0]))
            for row in rows:
                print(row)
        # 关闭客户端
        await dw_mysql_client_manager.close_client()

    # 测试查询dw库中的dim_customer表中的数据
    async def test_session_factory():
        # 初始化客户端
        dw_mysql_client_manager.init_client(app_config.db_dw)
        # 利用客户端查询数据表数据
        # 创建一个会话对象
        assert dw_mysql_client_manager.session_factory
        async with dw_mysql_client_manager.session_factory() as session:
            # 执行查询SQL
            # sql = 'select * from dim_customer limit 2'
            sql = 'select customer_name from dim_customer limit 2'
            result = await session.execute(text(sql))
            # 读取数据
            """
                result.all() 返回[row,row] 
                Row对象是包含当前行的字段值的可遍历的对象
                result.mappings().all() 返回[rowMapping,rowMapping] 
                Row对象是包含当前行的字段名和字段值的可遍历的对象
                result.scalars().all() 返回[val,val] 
                val是查询的第一列的字段值
            """
            # rows:list[Row] = result.all()
            # # print(rows,type(rows[0]))
            # for row in rows:
            #     for val in row:
            #         print(val)
            # print(rows[0].customer_name)

            # rows = result.mappings().all()
            # print(rows,type(rows[0]))
            # for row in rows:
            #     for key,val in row.items():
            #         print(key,val)
            # print(rows[0]['customer_name'])

            rows = result.scalars().all()
            print(rows, type(rows[0]))
            for row in rows:
                print(row)
        # 关闭客户端
        await dw_mysql_client_manager.close_client()


    # asyncio.run(test())
    asyncio.run(test_session_factory())
