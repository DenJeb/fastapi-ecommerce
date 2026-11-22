import sqlalchemy
import sqlalchemy.ext.asyncio
import sqlalchemy.orm

import app.modules.catalog.models as catalog_models


class CategoryRepository:
    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession):
        self.session = session

    async def get_by_id(self, category_id: str) -> catalog_models.Category | None:
        return await self.session.get(catalog_models.Category, category_id)

    async def get_by_slug(self, slug: str) -> catalog_models.Category | None:
        result = await self.session.execute(
            sqlalchemy.select(catalog_models.Category).where(
                catalog_models.Category.slug == slug
            )
        )
        return result.scalar_one_or_none()

    async def list_active(self) -> list[catalog_models.Category]:
        result = await self.session.execute(
            sqlalchemy.select(catalog_models.Category)
            .where(catalog_models.Category.is_active.is_(True))
            .order_by(catalog_models.Category.id)
        )
        return list(result.scalars().all())

    def add(self, category: catalog_models.Category) -> None:
        self.session.add(category)


class ProductRepository:
    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession):
        self.session = session

    async def get_by_id(self, product_id: int) -> catalog_models.Product | None:
        return await self.session.get(catalog_models.Product, product_id)

    async def get_by_slug(self, slug: str) -> catalog_models.Product | None:
        result = await self.session.execute(
            sqlalchemy.select(catalog_models.Product).where(
                catalog_models.Product.slug == slug
            )
        )
        return result.scalar_one_or_none()

    def _public_query(self):
        # 公开查询只加载上架 SKU；用 with_loader_criteria 过滤 ProductVariant。
        return sqlalchemy.select(catalog_models.Product).options(
            sqlalchemy.orm.selectinload(catalog_models.Product.variants),
            sqlalchemy.orm.with_loader_criteria(
                catalog_models.ProductVariant,
                catalog_models.ProductVariant.is_active.is_(True),
            ),
        )

    async def get_public_by_id(self, product_id: int) -> catalog_models.Product | None:
        result = await self.session.execute(
            self._public_query().where(
                catalog_models.Product.id == product_id,
                catalog_models.Product.status
                == catalog_models.ProductStatus.ACTIVE,
            )
        )
        return result.scalar_one_or_none()

    async def list_public(
        self,
        page: int,
        page_size: int,
        category_id: int | None,
    ) -> tuple[list[catalog_models.Product], int]:
        filters = [
            catalog_models.Product.status
            == catalog_models.ProductStatus.ACTIVE
        ]
        if category_id is not None:
            filters.append(
                catalog_models.Product.category_id == category_id
            )

        total = await self.session.scalar(
            sqlalchemy.select(sqlalchemy.func.count())
            .select_from(catalog_models.Product)
            .where(*filters)
        )

        result = await self.session.execute(
            self._public_query()
            .where(*filters)
            .order_by(catalog_models.Product.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), int(total or 0)

    def add(self, product: catalog_models.Product) -> None:
        self.session.add(product)

    async def get_variant_by_id(
        self, variant_id: int
    ) -> catalog_models.ProductVariant | None:
        return await self.session.get(
            catalog_models.ProductVariant, variant_id
        )

    async def get_variant_by_sku(self, sku: str) -> catalog_models.ProductVariant | None:
        result = await self.session.execute(
            sqlalchemy.select(catalog_models.ProductVariant).where(
                catalog_models.ProductVariant.sku == sku
            )
        )
        return result.scalar_one_or_none()

    def add_variant(self, variant: catalog_models.ProductVariant) -> None:
        self.session.add(variant)