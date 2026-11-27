import sqlalchemy
import sqlalchemy.ext.asyncio

import app.modules.inventory.models as inventory_models


class InventoryRepository:
    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession):
        self.session = session

    async def get_for_update(self, variant_id: int) -> inventory_models.Inventory | None:
        # 锁住库存行，后续检查和更新在同一个事务完成
        result = await self.session.execute(
            sqlalchemy.select(inventory_models.Inventory)
            .where(inventory_models.Inventory.variant_id == variant_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_by_variant_id(self, variant_id: int) -> inventory_models.Inventory | None:
        result = await self.session.execute(
            sqlalchemy.select(inventory_models.Inventory).where(
                inventory_models.Inventory.variant_id == variant_id
            )
        )
        return result.scalar_one_or_none()

    def add(self, inventory: inventory_models.Inventory) -> None:
        self.session.add(inventory)

    def add_movement(self, movement: inventory_models.InventoryMovement) -> None:
        self.session.add(movement)

    async def list_inventory(
        self,
        page: int,
        page_size: int,
        variant_id: int | None,
    ) -> tuple[list[inventory_models.Inventory], int]:
        count_stmt = sqlalchemy.select(
            sqlalchemy.func.count()
        ).select_from(inventory_models.Inventory)
        stmt = sqlalchemy.select(inventory_models.Inventory)

        if variant_id is not None:
            condition = inventory_models.Inventory.variant_id == variant_id
            count_stmt = count_stmt.where(condition)
            stmt = stmt.where(condition)

        total = await self.session.scalar(count_stmt)
        result = await self.session.execute(
            stmt.order_by(inventory_models.Inventory.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), int(total or 0)

    async def list_movements(
        self,
        page: int,
        page_size: int,
        inventory_id: int | None = None,
    ) -> tuple[list[inventory_models.InventoryMovement], int]:
        count_stmt = sqlalchemy.select(
            sqlalchemy.func.count()
        ).select_from(inventory_models.InventoryMovement)
        stmt = sqlalchemy.select(inventory_models.InventoryMovement)

        if inventory_id is not None:
            condition = inventory_models.InventoryMovement.inventory_id == inventory_id
            count_stmt = count_stmt.where(condition)
            stmt = stmt.where(condition)

        total = await self.session.scalar(count_stmt)
        result = await self.session.execute(
            stmt.order_by(inventory_models.InventoryMovement.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), int(total or 0)