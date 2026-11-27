import fastapi
import sqlalchemy.ext.asyncio

import app.db.dependencies
import app.modules.auth.dependencies
import app.modules.auth.models as auth_models
import app.modules.inventory.models as inventory_models
import app.modules.inventory.schemas as inventory_schemas
import app.modules.inventory.service

router = fastapi.APIRouter()


@router.get(
    "/admin/inventory",
    response_model=inventory_schemas.InventoryListResponse,
    tags=["Admin Inventory"],
    dependencies=[fastapi.Depends(app.modules.auth.dependencies.require_admin)],
)
async def list_inventory(
    page: int = fastapi.Query(default=1, ge=1),
    page_size: int = fastapi.Query(default=20, ge=1, le=100),
    variant_id: int | None = fastapi.Query(default=None),
    db_session: sqlalchemy.ext.asyncio.AsyncSession = fastapi.Depends(
        app.db.dependencies.get_db_session
    ),
) -> inventory_schemas.InventoryListResponse:
    service = app.modules.inventory.service.InventoryService(db_session)
    items, total = await service.list_inventory(page, page_size, variant_id)
    return inventory_schemas.InventoryListResponse(
        items=[
            inventory_schemas.InventoryResponse.model_validate(item)
            for item in items
        ],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post(
    "/admin/variants/{variant_id}/inventory-adjustments",
    response_model=inventory_schemas.InventoryResponse,
    tags=["Admin Inventory"],
)
async def adjust_inventory(
    variant_id: int,
    payload: inventory_schemas.InventoryAdjustmentRequest,
    current_user: auth_models.User = fastapi.Depends(
        app.modules.auth.dependencies.require_admin
    ),
    db_session: sqlalchemy.ext.asyncio.AsyncSession = fastapi.Depends(
        app.db.dependencies.get_db_session
    ),
) -> inventory_models.Inventory:
    service = app.modules.inventory.service.InventoryService(db_session)
    return await service.adjust(
        variant_id,
        payload.quantity_delta,
        payload.reason,
        actor_user_id=current_user.id,
    )


@router.get(
    "/admin/inventory-movements",
    response_model=inventory_schemas.InventoryMovementListResponse,
    tags=["Admin Inventory"],
    dependencies=[fastapi.Depends(app.modules.auth.dependencies.require_admin)],
)
async def list_inventory_movements(
    page: int = fastapi.Query(default=1, ge=1),
    page_size: int = fastapi.Query(default=20, ge=1, le=100),
    variant_id: int | None = fastapi.Query(default=None),
    db_session: sqlalchemy.ext.asyncio.AsyncSession = fastapi.Depends(
        app.db.dependencies.get_db_session
    ),
) -> inventory_schemas.InventoryMovementListResponse:
    service = app.modules.inventory.service.InventoryService(db_session)
    items, total = await service.list_movements(page, page_size, variant_id)
    return inventory_schemas.InventoryMovementListResponse(
        items=[
            inventory_schemas.InventoryMovementResponse.model_validate(item)
            for item in items
        ],
        page=page,
        page_size=page_size,
        total=total,
    )