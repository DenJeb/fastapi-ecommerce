import sqlalchemy.exc
import sqlalchemy.ext.asyncio

import app.core.exceptions
import app.modules.auth.models as auth_models
import app.modules.auth.repository
import app.modules.users.schemas as user_schemas


class UserService:
    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession):
        self.session = session
        self.repository = app.modules.auth.repository.UserRepository(session)

    async def update_profile(
        self,
        user_id: int,
        payload: user_schemas.UpdateUserRequest,
    ) -> auth_models.User:
        # 重新按 ID 查询
        user = await self.repository.get_by_id(user_id)
        if user is None:
            raise app.core.exceptions.ResourceNotFoundException(
                "User does not exist."
            )

        if payload.email is not None:
            email = payload.email.strip().lower()
            if email != user.email:
                existing = await self.repository.get_by_email(email)
                if existing is not None and existing.id != user.id:
                    raise app.core.exceptions.ConflictException(
                        message="Email is already registered.",
                        code="EMAIL_ALREADY_EXISTS",
                    )
                user.email = email

        if payload.username is not None:
            username = payload.username.strip()
            if username != user.username:
                existing = await self.repository.get_by_username(username)
                if existing is not None and existing.id != user.id:
                    raise app.core.exceptions.ConflictException(
                        message="Username is already taken.",
                        code="USERNAME_ALREADY_EXISTS",
                    )
                user.username = username

        try:
            await self.session.commit()
        except sqlalchemy.exc.IntegrityError as exc:
            await self.session.rollback()
            raise app.core.exceptions.ConflictException(
                message="Email or username is already registered.",
                code="USER_ALREADY_EXISTS",
            ) from exc

        return user