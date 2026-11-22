import sqlalchemy
import sqlalchemy.ext.asyncio

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