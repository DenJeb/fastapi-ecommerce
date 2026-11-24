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