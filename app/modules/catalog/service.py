import sqlalchemy.exc
import sqlalchemy.ext.asyncio

import app.core.exceptions
import app.modules.catalog.models as catalog_models
import app.modules.catalog.repository
import app.modules.catalog.schemas as catalog_schemas


class CategoryService:
    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession):
        self.session = session
        self.repository = app.modules.catalog.repository.CategoryRepository(session)

    async def list_active(self) -> list[catalog_models.Category]:
        return await self.repository.list_active()

    async def create(
        self, payload: catalog_schemas.CreateCategoryRequest
    ) -> catalog_models.Category:
        slug = payload.slug.strip().lower()

        if await self.repository.get_by_slug(slug) is not None:
            raise app.core.exceptions.ConflictException(
                message="Category slug already exists.",
                code="CATEGORY_SLUG_EXISTS",
            )

        if payload.parent_id is not None:
            parent = await self.repository.get_by_id(payload.parent_id)
            if parent is None:
                raise app.core.exceptions.ResourceNotFoundException(
                    "Parent category does not exist."
                )

        category = catalog_models.Category(
            name=payload.name.strip(),
            slug=slug,
            parent_id=payload.parent_id,
            is_active=payload.is_active,
        )
        self.repository.add(category)

        try:
            await self.session.commit()
        except sqlalchemy.exc.IntegrityError as exc:
            await self.session.rollback()
            raise app.core.exceptions.ConflictException(
                message="Category slug already exists.",
                code="CATEGORY_SLUG_EXISTS"
            ) from exc

        return category

    async def update(
        self,
        category_id: int,
        payload: catalog_schemas.UpdateCategoryRequest,
    ) -> catalog_models.Category:
        category = await self.repository.get_by_id(category_id)
        if category is None:
            raise app.core.exceptions.ResourceNotFoundException(
                "Category does not exist."
            )

        if payload.name is not None:
            category.name = payload.name.strip()

        if payload.slug is not None:
            slug = payload.slug.strip().lower()
            if slug != category.slug:
                existing = await self.repository.get_by_slug(slug)
                if existing is not None and existing.id != category.id:
                    raise app.core.exceptions.ConflictException(
                        message="Category slug already exists.",
                        code="CATEGORY_SLUG_EXISTS",
                    )
                category.slug = slug

        if "parent_id" in payload.model_fields_set:
            parent_id = payload.parent_id
            if parent_id is not None:
                parent = await self.repository.get_by_id(parent_id)
                if parent is None:
                    raise app.core.exceptions.ResourceNotFoundException(
                        "Parent category does not exist."
                    )
                if await self._would_create_cycle(category.id, parent_id):
                    raise app.core.exceptions.ConflictException(
                        message="Category hierarchy would form a cycle.",
                        code="CATEGORY_CYCLE",
                    )
            category.parent_id = parent_id

        if payload.is_active is not None:
            category.is_active = payload.is_active

        try:
            await self.session.commit()
        except sqlalchemy.exc.IntegrityError as exc:
            await self.session.rollback()
            raise app.core.exceptions.ConflictException(
                message="Category slug already exists.",
                code="CATEGORY_SLUG_EXISTS",
            ) from exc

        return category

    async def _would_create_cycle(
        self, category_id: int, parent_id: int
    ) -> bool:
        """从拟设置的父节点向上走"""
        current_id: int | None = parent_id
        while current_id is not None:
            if current_id == category_id:
                return True
            current = await self.repository.get_by_id(current_id)
            if current is None:
                return False
            current_id = current.parent_id
        return False


class ProductService:
    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession):
        self.session = session
        self.repository = app.modules.catalog.repository.ProductRepository(session)
        self.category_repository = (app.modules.catalog.repository.CategoryRepository(session))

    async def list_public(
        self,
        page: int,
        page_size: int,
        category_id: int | None,
    ) -> tuple[list[catalog_models.Product], int]:
        return await self.repository.list_public(
            page, page_size, category_id
        )

    async def get_public(self, product_id: int) -> catalog_models.Product:
        product = await self.repository.get_public_by_id(product_id)
        if product is None:
            raise app.core.exceptions.ResourceNotFoundException(
                "Product does not exist."
            )
        return product

    async def create(
        self, payload: catalog_schemas.CreateProductRequest
    ) -> catalog_models.Product:
        if (await self.category_repository.get_by_id(payload.category_id) is None):
            raise app.core.exceptions.ResourceNotFoundException(
                "Category does not exist."
            )

        slug = payload.slug.strip().lower()
        if await self.repository.get_by_slug(slug) is not None:
            raise app.core.exceptions.ConflictException(
                message="Product slug already exists.",
                code="PRODUCT_SLUG_EXISTS",
            )

        product = catalog_models.Product(
            category_id=payload.category_id,
            name=payload.name.strip(),
            slug=slug,
            description=payload.description,
            status=payload.status,
            # 初始化空集合，避免返回响应时触发 async 懒加载。
            variants=[],
        )
        self.repository.add(product)

        try:
            await self.session.commit()
        except sqlalchemy.exc.IntegrityError as exc:
            await self.session.rollback()
            raise app.core.exceptions.ConflictException(
                message="Product slug already exists.",
                code="PRODUCT_SLUG_EXISTS",
            ) from exc

        return product

    async def update(
        self,
        product_id: int,
        payload: catalog_schemas.UpdateProductRequest,
    ) -> catalog_models.Product:
        product = await self.repository.get_by_id(product_id)
        if product is None:
            raise app.core.exceptions.ResourceNotFoundException(
                "Product does not exist."
            )

        if payload.category_id is not None:
            if (
                await self.category_repository.get_by_id(
                    payload.category_id
                )
                is None
            ):
                raise app.core.exceptions.ResourceNotFoundException(
                    "Category does not exist."
                )
            product.category_id = payload.category_id

        if payload.name is not None:
            product.name = payload.name.strip()

        if payload.slug is not None:
            slug = payload.slug.strip().lower()
            if slug != product.slug:
                existing = await self.repository.get_by_slug(slug)
                if (
                    existing is not None
                    and existing.id != product.id
                ):
                    raise app.core.exceptions.ConflictException(
                        message="Product slug already exists.",
                        code="PRODUCT_SLUG_EXISTS",
                    )
                product.slug = slug

        # 显式传 null 表示清空描述。
        if "description" in payload.model_fields_set:
            product.description = payload.description

        if payload.status is not None:
            product.status = payload.status

        try:
            await self.session.commit()
        except sqlalchemy.exc.IntegrityError as exc:
            await self.session.rollback()
            raise app.core.exceptions.ConflictException(
                message="Product slug already exists.",
                code="PRODUCT_SLUG_EXISTS",
            ) from exc

        return product

    async def create_variant(
        self,
        product_id: int,
        payload: catalog_schemas.CreateVariantRequest,
    ) -> catalog_models.ProductVariant:
        product = await self.repository.get_by_id(product_id)
        if product is None:
            raise app.core.exceptions.ResourceNotFoundException(
                "Product does not exist."
            )

        sku = payload.sku.strip()
        if await self.repository.get_variant_by_sku(sku) is not None:
            raise app.core.exceptions.ConflictException(
                message="Variant SKU already exists.",
                code="VARIANT_SKU_EXISTS",
            )

        variant = catalog_models.ProductVariant(
            product_id=product.id,
            sku=sku,
            name=payload.name.strip(),
            price=payload.price,
            is_active=payload.is_active,
        )
        self.repository.add_variant(variant)

        try:
            await self.session.commit()
        except sqlalchemy.exc.IntegrityError as exc:
            await self.session.rollback()
            raise app.core.exceptions.ConflictException(
                message="Variant SKU already exists.",
                code="VARIANT_SKU_EXISTS",
            ) from exc

        return variant

    async def update_variant(
        self,
        variant_id: int,
        payload: catalog_schemas.UpdateVariantRequest,
    ) -> catalog_models.ProductVariant:
        variant = await self.repository.get_variant_by_id(variant_id)
        if variant is None:
            raise app.core.exceptions.ResourceNotFoundException(
                "Variant does not exist."
            )

        if payload.sku is not None:
            sku = payload.sku.strip()
            if sku != variant.sku:
                existing = await self.repository.get_variant_by_sku(sku)
                if (
                    existing is not None
                    and existing.id != variant.id
                ):
                    raise app.core.exceptions.ConflictException(
                        message="Variant SKU already exists.",
                        code="VARIANT_SKU_EXISTS",
                    )
                variant.sku = sku

        if payload.name is not None:
            variant.name = payload.name.strip()

        if payload.price is not None:
            variant.price = payload.price

        if payload.is_active is not None:
            variant.is_active = payload.is_active

        try:
            await self.session.commit()
        except sqlalchemy.exc.IntegrityError as exc:
            await self.session.rollback()
            raise app.core.exceptions.ConflictException(
                message="Variant SKU already exists.",
                code="VARIANT_SKU_EXISTS",
            ) from exc

        return variant