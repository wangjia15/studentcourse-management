"""
数据库会话辅助工具
为批量处理和其他后台任务提供数据库会话管理
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

settings = get_settings()

# 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=300,
)

# 创建会话工厂
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class DatabaseHelper:
    """数据库操作辅助类"""

    @staticmethod
    async def execute_with_session(
        func,
        *args,
        **kwargs
    ):
        """在会话中执行函数"""
        async with AsyncSessionLocal() as session:
            try:
                result = await func(session, *args, **kwargs)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise

    @staticmethod
    async def batch_insert(
        session: AsyncSession,
        model_class,
        data_list: list,
        batch_size: int = 1000
    ):
        """批量插入数据"""
        try:
            for i in range(0, len(data_list), batch_size):
                batch = data_list[i:i + batch_size]
                session.add_all([model_class(**data) for data in batch])
                await session.flush()

            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e

    @staticmethod
    async def batch_update(
        session: AsyncSession,
        model_class,
        updates: list,
        batch_size: int = 1000
    ):
        """批量更新数据"""
        try:
            for i in range(0, len(updates), batch_size):
                batch = updates[i:i + batch_size]
                for update_data in batch:
                    # 查找记录并更新
                    record = await session.get(model_class, update_data['id'])
                    if record:
                        for key, value in update_data.items():
                            if key != 'id':
                                setattr(record, key, value)

                await session.flush()

            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e

    @staticmethod
    async def execute_raw_sql(
        session: AsyncSession,
        sql: str,
        params: dict = None
    ):
        """执行原生SQL"""
        try:
            from sqlalchemy import text
            result = await session.execute(text(sql), params or {})
            await session.commit()
            return result
        except Exception as e:
            await session.rollback()
            raise e