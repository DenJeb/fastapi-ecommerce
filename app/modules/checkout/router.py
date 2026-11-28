import fastapi
import sqlalchemy.ext.asyncio

import app.db.dependencies
import app.modules.auth.dependencies
import app.modules.auth.models as auth_models
import app.modules.checkout.schemas as checkout_schemas
import app.modules.checkout.service
import app.modules.orders.models as order_models
import app.modules.orders.schemas as order_schemas

router = fastapi.APIRouter(prefix="/checkout", tags=["Checkout"])


@router.post(
    "/preview",
    response_model=checkout_schemas.CheckoutPreviewResponse,
)
async def preview_checkout(
    current_user: auth_models.User = fastapi.Depends(
        app.modules.auth.dependencies.get_current_user
    ),
    db_session: sqlalchemy.ext.asyncio.AsyncSession = fastapi.Depends(
        app.db.dependencies.get_db_session
    ),
) -> checkout_schemas.CheckoutPreviewResponse:
    service = app.modules.checkout.service.CheckoutService(db_session)
    return await service.preview(current_user.id)


@router.post(
    "/orders",
    response_model=order_schemas.OrderResponse,
    status_code=201,
)
async def create_order(
    response: fastapi.Response,
    idempotency_key: str | None = fastapi.Header(
        default=None,
        alias="Idempotency-Key",
        max_length=64,
    ),
    current_user: auth_models.User = fastapi.Depends(
        app.modules.auth.dependencies.get_current_user
    ),
    db_session: sqlalchemy.ext.asyncio.AsyncSession = fastapi.Depends(
        app.db.dependencies.get_db_session
    ),
) -> order_models.Order:
    service = app.modules.checkout.service.CheckoutService(db_session)
    order, created = await service.create_order(
        current_user.id, idempotency_key
    )
    if not created:
        response.status_code = 200
    return order