import sqlalchemy.exc
import sqlalchemy.ext.asyncio

import app.core.config
import app.core.exceptions
import app.core.security
import app.modules.auth.models as auth_models
import app.modules.auth.repository
import app.modules.auth.schemas as auth_schemas

DEFAULT_ROLE_NAME = "user"
ADMIN_ROLE_NAME = "admin"


class AuthService:
    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession):
        self.session = session
        self.repository = app.modules.auth.repository.UserRepository(session)

    async def register(self, payload: auth_schemas.RegisterRequest) -> auth_models.User:
        email = payload.email.strip().lower()
        username = payload.username.strip()

        if await self.repository.get_by_email(email) is not None:
            raise app.core.exceptions.ConflictException(
                message="Email is already registered.",
                code="EMAIL_ALREADY_EXISTS",
            )
        if await self.repository.get_by_username(username) is not None:
            raise app.core.exceptions.ConflictException(
                message="Username is already taken.",
                code="USERNAME_ALREADY_EXISTS",
            )

        role = await self.repository.get_role_by_name(DEFAULT_ROLE_NAME)
        if role is None:
            # 服务端配置缺失
            raise RuntimeError(f"Default role '{DEFAULT_ROLE_NAME}' is not seeded.")

        user = auth_models.User(
            email=email,
            username=username,
            password_hash=app.core.security.hash_password(payload.password),
        )
        user.roles.append(role)
        self.repository.add(user)

        try:
            await self.session.commit()
        except sqlalchemy.exc.IntegrityError as exc:
            # 并发注册唯一约束是最后一道防线
            await self.session.rollback()
            raise app.core.exceptions.ConflictException(
                message="Email or username is already registered.",
                code="USER_ALREADY_EXISTS",
            ) from exc

        return user

    async def authenticate(self, identifier: str, password: str) -> auth_models.User:
        user = await self.repository.get_by_indentifier(identifier.strip())

        # 用户不存在和密码错误返回同一个错误
        if user is None or app.core.security.verify_password(
            password, user.password_hash
        ):
            raise app.core.exceptions.UnauthorizedException(
                message="Account is disabled",
                code="ACCOUNT_DISABLED",
            )

        return user

    def issue_token(self, user: auth_models.User) -> auth_schemas.TokenResponse:
        token = app.core.security.create_access_token(str(user.id))
        return auth_schemas.TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=app.core.config.settings.access_token_expire_minutes * 60,
        )

    async def get_user_by_id(self, user_id: int) -> auth_models.User:
        user = await self.repository.get_by_id(user_id)
        if user is None:
            raise app.core.exceptions.UnauthorizedException(
                message="User no longer exists.",
                code="INVALID_TOKEN"
            )
        if not user.is_active:
            raise app.core.exceptions.ForbiddenException(
                message="Account is disabled.",
                code="ACCOUNT_DISABLED",
            )
        return user

    def has_role(user: auth_models.User, role_name: str) -> bool:
        return any(role.name == role_name for role in user.roles)
