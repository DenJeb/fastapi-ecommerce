import sqlalchemy
import sqlalchemy.ext.asyncio

import app.modules.auth.models as auth_models


class UserRepository:
    """用户/角色数据(只查询和挂起对象，不提交事务)"""

    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> auth_models.User | None:
        return await self.session.get(auth_models.User, user_id)

    async def get_by_email(self, email: str) -> auth_models.User | None:
        result = await self.session.execute(
            sqlalchemy.select(auth_models.User).where(
                auth_models.User.email == email
            )
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> auth_models.User | None:
        result = await self.session.execute(
            sqlalchemy.select(auth_models.User).where(
                auth_models.User.username == username
            )
        )
        return result.scalar_one_or_none()

    async def get_by_identifier(self, identifier: str) -> auth_models.User | None:
        result = await self.session.execute(
            sqlalchemy.select(auth_models.User).where(
                sqlalchemy.or_(
                    auth_models.User.email == identifier,
                    auth_models.User.username == identifier,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_role_by_name(self, name: str) -> auth_models.Role | None:
        result = await self.session.execute(
            sqlalchemy.select(auth_models.Role).where(
                auth_models.Role.name == name
            )
        )
        return result.scalar_one_or_none()

    def add(self, user: auth_models.User) -> None:
        self.session.add(user)