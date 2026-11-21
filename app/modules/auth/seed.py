import sqlalchemy
import sqlalchemy.ext.asyncio

import app.modules.auth.models as auth_models

DEFAULT_ROLES = (
    ("admin", "Administrator"),
    ("user", "Regular user"),
)


async def ensure_default_roles(session: sqlalchemy.ext.asyncio.AsyncSession) -> None:
    """幂等地插入默认角色，调用方 commit"""
    for name, description in DEFAULT_ROLES:
        existing = await session.scalar(
            sqlalchemy.select(auth_models.Role).where(
                auth_models.Role.name == name
            )
        )
        if existing is None:
            session.add(
                auth_models.Role(name=name, description=description)
            )

    await session.flush()