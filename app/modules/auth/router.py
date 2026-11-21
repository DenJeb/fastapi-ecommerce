import fastapi
import sqlalchemy.ext.asyncio
import starlette.status

import app.db.dependencies
import app.modules.auth.models as auth_models
import app.modules.auth.schemas as auth_schemas
import app.modules.auth.service

router = fastapi.APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=auth_schemas.UserResponse,
    status_code=starlette.status.HTTP_201_CREATED,
)
async def register(
    payload: auth_schemas.RegisterRequest,
    db_session: sqlalchemy.ext.asyncio.AsyncSession = fastapi.Depends(
        app.db.dependencies.get_db_session
    ),
) -> auth_models.User:
    service = app.modules.auth.service.AuthService(db_session)
    return await service.register(payload)


@router.post(
    "/login",
    response_model=auth_schemas.TokenResponse,
)
async def login(
    payload: auth_schemas.LoginRequest,
    db_session: sqlalchemy.ext.asyncio.AsyncSession = fastapi.Depends(
        app.db.dependencies.get_db_session
    ),
) -> auth_schemas.TokenResponse:
    service = app.modules.auth.service.AuthService(db_session)
    user = await service.authenticate(payload.identifier, payload.password)
    return service.issue_token(user)