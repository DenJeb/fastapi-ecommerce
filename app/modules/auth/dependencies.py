import fastapi
import fastapi.security
import sqlalchemy.ext.asyncio

import app.core.exceptions
import app.core.security
import app.db.dependencies
import app.modules.auth.models as auth_models
import app.modules.auth.service

# 缺少 token 时返回 None
bearer_schemas = fastapi.security.HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: fastapi.security.HTTPAuthorizationCredentials | None = fastapi.Depends(
        bearer_schemas
    ),
    db_session: sqlalchemy.ext.asyncio.AsyncSession = fastapi.Depends(
        app.db.dependencies.get_db_session
    ),
) -> auth_models.User:
    """从 Bearer token 解析当前用户，所有认证失败统一映射为 401"""
    if credentials is None:
        raise app.core.exceptions.UnauthorizedException(
            message="Authentication is required.",
            code="UNAUTHORIZED",
        )

    try:
        payload = app.core.security.decode_access_token(credentials.credentials)
    except app.core.security.InvalidTokenError as exc:
        raise app.core.exceptions.UnauthorizedException(
            message="Invalid or expired token.",
            code="INVALID_TOKEN",
        ) from exc

    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise app.core.exceptions.UnauthorizedException(
            message="Invalid token subject.",
            code="INVALID_TOKEN",
        ) from exc

    service = app.modules.auth.service.AuthService(db_session)
    return await service.get_user_by_id(user_id)


async def require_admin(
    current_user: auth_models.User = fastapi.Depends(get_current_user),
) -> auth_models.User:
    """已认证且拥有 admin 角色通过"""
    if not app.modules.auth.service.has_role(
        current_user, app.modules.auth.service.ADMIN_ROLE_NAME
    ):
        raise app.core.exceptions.ForbiddenException(
            message="Administrator privileges are required.",
            code="ADMIN_REQUIRED",
        )
    return current_user