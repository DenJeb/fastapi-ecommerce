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


@router.get(
    "/products",
    response_model=catalog_schemas.ProductListResponse,
    tags=["Products"],
)
async def list_products(
    page: int = fastapi.Query(default=1, ge=1),
    page_size: int = fastapi.Query(default=20, ge=1, le=100),
    category_id: int | None = fastapi.Query(default=None),
    db_session: sqlalchemy.ext.asyncio.AsyncSession = fastapi.Depends(app.db.dependencies.get_db_session),
) -> catalog_schemas.ProductListResponse:
    service = app.modules.catalog.service.ProductService(db_session)
    products, total = await service.list_public(
        page, page_size, category_id
    )
    return catalog_schemas.ProductListResponse(
        items=[
            catalog_schemas.ProductResponse.model_validate(product)
            for product in products
        ],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/products/{product_id}",
    response_model=catalog_schemas.ProductResponse,
    tags=["Products"],
)
async def get_product(
    product_id: int,
    db_session: sqlalchemy.ext.asyncio.AsyncSession = fastapi.Depends(
        app.db.dependencies.get_db_session
    ),
) -> catalog_models.Product:
    service = app.modules.catalog.service.ProductService(db_session)
    return await service.get_public(product_id)


@router.post(
    "/admin/products",
    response_model=catalog_schemas.ProductResponse,
    status_code=201,
    tags=["Admin Products"],
    dependencies=[fastapi.Depends(app.modules.auth.dependencies.require_admin)],
)
async def create_product(
    payload: catalog_schemas.CreateProductRequest,
    db_session: sqlalchemy.ext.asyncio.AsyncSession = fastapi.Depends(
        app.db.dependencies.get_db_session
    ),
) -> catalog_models.Product:
    service = app.modules.catalog.service.ProductService(db_session)
    return await service.create(payload)


@router.patch(
    "/admin/products/{product_id}",
    response_model=catalog_schemas.ProductResponse,
    tags=["Admin Products"],
    dependencies=[fastapi.Depends(app.modules.auth.dependencies.require_admin)],
)
async def update_product(
    product_id: int,
    payload: catalog_schemas.UpdateProductRequest,
    db_session: sqlalchemy.ext.asyncio.AsyncSession = fastapi.Depends(
        app.db.dependencies.get_db_session
    ),
) -> catalog_models.Product:
    service = app.modules.catalog.service.ProductService(db_session)
    return await service.update(product_id, payload)


@router.post(
    "/admin/products/{product_id}/variants",
    response_model=catalog_schemas.VariantResponse,
    status_code=201,
    tags=["Admin Products"],
    dependencies=[fastapi.Depends(app.modules.auth.dependencies.require_admin)],
)
async def create_variant(
    product_id: int,
    payload: catalog_schemas.CreateVariantRequest,
    db_session: sqlalchemy.ext.asyncio.AsyncSession = fastapi.Depends(
        app.db.dependencies.get_db_session
    ),
) -> catalog_models.ProductVariant:
    service = app.modules.catalog.service.ProductService(db_session)
    return await service.create_variant(product_id, payload)


@router.patch(
    "/admin/variants/{variant_id}",
    response_model=catalog_schemas.VariantResponse,
    tags=["Admin Products"],
    dependencies=[fastapi.Depends(app.modules.auth.dependencies.require_admin)],
)
async def update_variant(
    variant_id: int,
    payload: catalog_schemas.UpdateVariantRequest,
    db_session: sqlalchemy.ext.asyncio.AsyncSession = fastapi.Depends(
        app.db.dependencies.get_db_session
    ),
) -> catalog_models.ProductVariant:
    service = app.modules.catalog.service.ProductService(db_session)
    return await service.update_variant(variant_id, payload)