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