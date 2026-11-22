import asyncio
import os

# 必须在导入 app 之前设置
# settings 是模块级单例，导入时读取环境变量
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "false"
os.environ["DB_NAME"] = "saleor_backend_test"
os.environ["JWT_SECRET_KEY"] = "test-only-jwt-secret-key-with-32-bytes"

import fastapi.testclient
import pytest
import sqlalchemy
import sqlalchemy.ext.asyncio
import sqlalchemy.pool

import app.db.session
import app.main
import app.models
import app.modules.auth.models as auth_models
import app.modules.auth.seed

TEST_DB_NAME = "saleor_backend_test"

# 只允许对 _test 结尾的数据库执行 DROP/CREATE
if app.db.session.database_url.database != TEST_DB_NAME:
    raise RuntimeError(
        f"Refusing to run tests against database: "
        f"{app.db.session.database_url.database!r}"
    )


@pytest.fixture(scope="session", autouse=True)
def prepare_test_database():
    """整个测试会话开始前重建测试库并建表"""

    async def reset_database():
        # 显式重建一个不带 database 的连接串，先连到 MySQL 服务器本身。
        admin_url = sqlalchemy.URL.create(
            drivername=app.db.session.database_url.drivername,
            username=app.db.session.database_url.username,
            password=app.db.session.database_url.password,
            host=app.db.session.database_url.host,
            port=app.db.session.database_url.port,
        )
        
        admin_engine = sqlalchemy.ext.asyncio.create_async_engine(
            admin_url,
            poolclass=sqlalchemy.pool.NullPool,
            isolation_level="AUTOCOMMIT", 
        )

        try:
            async with admin_engine.connect() as connection:
                await connection.execute(
                    sqlalchemy.text(f"DROP DATABASE IF EXISTS `{TEST_DB_NAME}`")
                )
                await connection.execute(
                    sqlalchemy.text(
                        f"CREATE DATABASE `{TEST_DB_NAME}` "
                        "CHARACTER SET utf8mb4"
                    )
                )
        finally:
            await admin_engine.dispose()

    async def create_schema():
        schema_engine = sqlalchemy.ext.asyncio.create_async_engine(
            app.db.session.database_url,
            poolclass=sqlalchemy.pool.NullPool,
        )
        try:
            async with schema_engine.begin() as connection:
                await connection.run_sync(
                    app.db.session.Base.metadata.create_all
                )
            # 默认角色是参考数据
            factory = sqlalchemy.ext.asyncio.async_sessionmaker(
                schema_engine,
                expire_on_commit=False,
            )
            async with factory() as session:
                await app.modules.auth.seed.ensure_default_roles(session)
                await session.commit()
        finally:
            await schema_engine.dispose()

    asyncio.run(reset_database())
    asyncio.run(create_schema())

    yield


@pytest.fixture(autouse=True)
def clean_database():
    """每个测试结束后清空业务表，避免测试之间共享数据"""
    yield

    async def truncate_tables():
        engine = sqlalchemy.ext.asyncio.create_async_engine(
            app.db.session.database_url,
            poolclass=sqlalchemy.pool.NullPool,
            isolation_level="AUTOCOMMIT",
        )
        try:
            async with engine.connect() as connection:
                await connection.execute(
                    sqlalchemy.text("SET FOREIGN_KEY_CHECKS=0")
                )
                for table in reversed(
                    app.db.session.Base.metadata.sorted_tables
                ):
                    if table.name == "roles":
                        continue
                    await connection.execute(
                        sqlalchemy.text(f"TRUNCATE TABLE `{table.name}`")
                    )
                await connection.execute(
                    sqlalchemy.text("SET FOREIGN_KEY_CHECKS=1")
                )
        finally:
            await engine.dispose()

    asyncio.run(truncate_tables())


@pytest.fixture
def client():
    # with 会在用例结束时关闭 TestClient 的事件循环
    with fastapi.testclient.TestClient(app.main.application) as test_client:
        yield test_client


def _run_db(action) -> None:
    async def main():
        engine = sqlalchemy.ext.asyncio.create_async_engine(
            app.db.session.database_url,
            poolclass=sqlalchemy.pool.NullPool,
        )
        factory = sqlalchemy.ext.asyncio.async_sessionmaker(
            engine,
            expire_on_commit=False,
        )
        try:
            async with factory() as session:
                await action(session)
        finally:
            await engine.dispose()

    asyncio.run(main())


def _grant_admin(email: str) -> None:
    async def action(session):
        user = await session.scalar(
            sqlalchemy.select(auth_models.User).where(
                auth_models.User.email == email
            )
        )
        role = await session.scalar(
            sqlalchemy.select(auth_models.Role).where(
                auth_models.Role.name == "admin"
            )
        )
        assert user is not None
        assert role is not None
        user.roles.append(role)
        await session.commit()

    _run_db(action)


@pytest.fixture
def admin_headers(client):
    email = "admin@example.com"
    password = "password123"

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": "admin_user",
            "password": password,
        },
    )
    assert response.status_code == 201

    _grant_admin(email)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": email,
            "password": password,
        },
    )
    assert response.status_code == 200

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}