import asyncio
import logging.config

import alembic.context

import app.db.session
import app.models.migration_test


# 获取 Alembic 配置对象
config = alembic.context.config

# 配置日志
if config.config_file_name is not None:
    logging.config.fileConfig(config.config_file_name)

# 关联项目中的 ORM 元数据
target_metadata = app.db.session.Base.metadata


def run_migrations_offline():
    """离线模式：生成迁移 SQL，不建立数据库连接。"""
    url = app.db.session.database_url.render_as_string(
        hide_password=False
    )

    alembic.context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with alembic.context.begin_transaction():
        alembic.context.run_migrations()


def do_run_migrations(connection):
    """在同步连接上下文中执行迁移配置。"""
    alembic.context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with alembic.context.begin_transaction():
        alembic.context.run_migrations()


async def run_migrations_online():
    """在线模式：使用项目已有的异步 Engine 执行迁移。"""
    try:
        async with app.db.session.engine.connect() as connection:
            await connection.run_sync(do_run_migrations)
    finally:
        await app.db.session.engine.dispose()


if alembic.context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
