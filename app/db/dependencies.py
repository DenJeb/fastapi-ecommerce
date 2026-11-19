import collections.abc

import sqlalchemy.ext.asyncio

import app.db.session


async def get_db_session() -> collections.abc.AsyncGenerator[
    sqlalchemy.ext.asyncio.AsyncSession, None
]:
    """提供数据库 Session，并在请求结束后关闭。"""
    async with app.db.session.async_session_factory() as session:
        yield session