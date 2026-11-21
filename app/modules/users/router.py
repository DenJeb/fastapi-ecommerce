import fastapi
import sqlalchemy.ext.asyncio

import app.db.dependencies
import app.modules.auth.dependencies
import app.modules.auth.models as auth_models
import app.modules.auth.schemas as auth_schemas
import app.modules.users.schemas as user_schemas
import app.modules.users.service

router = fastapi.APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=auth_schemas.UserResponse)
async def get_me(
    current_user: auth_models.User = fastapi.Depends(
        app.modules.auth.dependencies.get_current_user
    ),
) -> auth_models.User:
    return current_user


@router.patch("/me", response_model=auth_schemas.UserResponse)
async def update_me(
    payload: user_schemas.UpdateUserRequest,
    current_user: auth_models.User = fastapi.Depends(
        app.modules.auth.dependencies.get_current_user
    ),
    db_session: sqlalchemy.ext.asyncio.AsyncSession = fastapi.Depends(
        app.db.dependencies.get_db_session
    ),
) -> auth_models.User:
    service = app.modules.users.service.UserService(db_session)
    return await service.update_profile(current_user.id, payload)