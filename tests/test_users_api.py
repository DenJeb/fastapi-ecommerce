import asyncio

import fastapi
import fastapi.testclient
import pytest
import sqlalchemy
import sqlalchemy.ext.asyncio
import sqlalchemy.pool

import app.core.exception_handlers
import app.core.middleware
import app.db.session
import app.modules.auth.dependencies
import app.modules.auth.models as auth_models

PASSWORD = "password123"


def register_user(client, email="user@example.com", username="user_1"):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": username,
            "password": PASSWORD,
        },
    )
    assert response.status_code == 201
    return response.json()


def login_user(client, identifier="user@example.com"):
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": identifier, "password": PASSWORD},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _run_db(action) -> None:
    async def _main():
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

    asyncio.run(_main())


def deactivate_user(email: str) -> None:
    async def action(session):
        user = await session.scalar(
            sqlalchemy.select(auth_models.User).where(
                auth_models.User.email == email
            )
        )
        assert user is not None
        user.is_active = False
        await session.commit()

    _run_db(action)


def grant_admin(email: str) -> None:
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


# 独立测试应用：验证 require_admin，不把测试路由塞进生产应用。
admin_app = fastapi.FastAPI()
app.core.middleware.register_middlewares(admin_app)
app.core.exception_handlers.register_exception_handlers(admin_app)


@admin_app.get("/admin-check")
async def admin_check(
    user: auth_models.User = fastapi.Depends(
        app.modules.auth.dependencies.require_admin
    ),
):
    return {"ok": True}


@pytest.fixture
def admin_client():
    with fastapi.testclient.TestClient(admin_app) as client:
        yield client


def test_me_requires_authentication(client):
    response = client.get("/api/v1/users/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_me_rejects_invalid_token(client):
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer not-a-jwt"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"


def test_me_returns_current_user(client):
    register_user(client)
    token = login_user(client)

    response = client.get("/api/v1/users/me", headers=auth_headers(token))

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "user@example.com"
    assert body["username"] == "user_1"
    assert [role["name"] for role in body["roles"]] == ["user"]


def test_me_rejects_inactive_user(client):
    register_user(client)
    token = login_user(client)
    deactivate_user("user@example.com")

    response = client.get("/api/v1/users/me", headers=auth_headers(token))

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACCOUNT_DISABLED"


def test_login_rejects_inactive_user(client):
    register_user(client)
    deactivate_user("user@example.com")

    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "user@example.com", "password": PASSWORD},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACCOUNT_DISABLED"


def test_update_profile_username(client):
    register_user(client)
    token = login_user(client)

    response = client.patch(
        "/api/v1/users/me",
        headers=auth_headers(token),
        json={"username": "new_username"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == "new_username"


def test_update_profile_rejects_duplicate_username(client):
    register_user(client)
    register_user(
        client,
        email="other@example.com",
        username="other_user",
    )
    token = login_user(client)

    response = client.patch(
        "/api/v1/users/me",
        headers=auth_headers(token),
        json={"username": "other_user"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "USERNAME_ALREADY_EXISTS"


def test_update_profile_rejects_empty_payload(client):
    register_user(client)
    token = login_user(client)

    response = client.patch(
        "/api/v1/users/me",
        headers=auth_headers(token),
        json={},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_admin_check_rejects_regular_user(client, admin_client):
    register_user(client)
    token = login_user(client)

    response = admin_client.get(
        "/admin-check",
        headers=auth_headers(token),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ADMIN_REQUIRED"


def test_admin_check_allows_admin(client, admin_client):
    register_user(client)
    token = login_user(client)
    grant_admin("user@example.com")

    response = admin_client.get(
        "/admin-check",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}