import fastapi
import sqlalchemy.ext.asyncio

import app.db.dependencies
import app.modules.auth.dependencies
import app.modules.auth.models as auth_models
import app.modules.cart.models as cart_models
import app.modules.cart.schemas as cart_schemas
import app.modules.cart.service

router = fastapi.APIRouter(prefix="/cart", tags=["Cart"])


@router.get("", response_model=cart_schemas.CartResponse)
async def get_cart(
    current_user: auth_models.User = fastapi.Depends(
        app.modules.auth.dependencies.get_current_user
    ),
    db_session: sqlalchemy.ext.asyncio.AsyncSession = fastapi.Depends(
        app.db.dependencies.get_db_session
    ),
) -> cart_models.Cart:
    service = app.modules.cart.service.CartService(db_session)
    return await service.get_or_create(current_user.id)


@router.post("/items", response_model=cart_schemas.CartResponse)
async def add_cart_item(
    payload: cart_schemas.AddCartItemRequest,
    current_user: auth_models.User = fastapi.Depends(
        app.modules.auth.dependencies.get_current_user
    ),
    db_session: sqlalchemy.ext.asyncio.AsyncSession = fastapi.Depends(
        app.db.dependencies.get_db_session
    ),
) -> cart_models.Cart:
    service = app.modules.cart.service.CartService(db_session)
    return await service.add_item(
        current_user.id, payload.variant_id, payload.quantity
    )


@router.patch("/items/{item_id}", response_model=cart_schemas.CartResponse)
async def update_cart_item(
    item_id: int,
    payload: cart_schemas.UpdateCartItemRequest,
    current_user: auth_models.User = fastapi.Depends(
        app.modules.auth.dependencies.get_current_user
    ),
    db_session: sqlalchemy.ext.asyncio.AsyncSession = fastapi.Depends(
        app.db.dependencies.get_db_session
    ),
) -> cart_models.Cart:
    service = app.modules.cart.service.CartService(db_session)
    return await service.update_item(
        current_user.id, item_id, payload.quantity
    )


@router.delete("/items/{item_id}", response_model=cart_schemas.CartResponse)
async def remove_cart_item(
    item_id: int,
    current_user: auth_models.User = fastapi.Depends(
        app.modules.auth.dependencies.get_current_user
    ),
    db_session: sqlalchemy.ext.asyncio.AsyncSession = fastapi.Depends(
        app.db.dependencies.get_db_session
    ),
) -> cart_models.Cart:
    service = app.modules.cart.service.CartService(db_session)
    return await service.remove_item(current_user.id, item_id)