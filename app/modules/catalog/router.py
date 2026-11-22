import fastapi
import sqlalchemy.ext.asyncio

import app.db.dependencies
import app.modules.auth.dependencies
import app.modules.catalog.models as catalog_models
import app.modules.catalog.schemas as catalog_schemas
import app.modules.catalog.service

router = fastapi.APIRouter()


@router.get(
    "/categories",
    response_model=list[catalog_schemas.CategoryResponse],
    tags=["Categories"],
)
async def list_categories(
    db_session: sqlalchemy.ext.asyncio.AsyncSession = fastapi.Depends(
        app.db.dependencies.get_db_session
    ),
) -> list[catalog_models.Category]:
    service = app.modules.catalog.service.CategoryService(db_session)
    return await service.list_active()


@router.post(
    "/admin/categories",
    response_model=catalog_schemas.CategoryResponse,
    status_code=201,
    tags=["Admin Categories"],
    dependencies=[fastapi.Depends(app.modules.auth.dependencies.require_admin)],
)
async def create_category(
    payload: catalog_schemas.CreateCategoryRequest,
    db_session: sqlalchemy.ext.asyncio.AsyncSession = fastapi.Depends(
        app.db.dependencies.get_db_session
    ),
) -> catalog_models.Category:
    service = app.modules.catalog.service.CategoryService(db_session)
    return await service.create(payload)


@router.patch(
    "/admin/categories/{category_id}",
    response_model=catalog_schemas.CategoryResponse,
    tags=["Admin Categories"],
    dependencies=[fastapi.Depends(app.modules.auth.dependencies.require_admin)]
)
async def update_category(
    category_id: int,
    payload: catalog_schemas.UpdateCategoryRequest,
    db_session: sqlalchemy.ext.asyncio.AsyncSession = fastapi.Depends(
        app.db.dependencies.get_db_session
    ),
) -> catalog_models.Category:
    service = app.modules.catalog.service.CategoryService(db_session)
    return await service.update(category_id, payload)