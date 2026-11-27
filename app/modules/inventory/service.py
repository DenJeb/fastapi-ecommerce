import sqlalchemy
import sqlalchemy.exc
import sqlalchemy.ext.asyncio

import app.core.exceptions
import app.modules.catalog.models as catalog_models
import app.modules.inventory.models as inventory_models
import app.modules.inventory.repository


class InventoryService:
    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession):
        self.session = session
        self.repository = app.modules.inventory.repository.InventoryRepository(session)

    async def get_available(self, variant_id: int) -> int:
        inventory = await self.repository.get_by_variant_id(variant_id)
        if inventory is None:
            return 0
        return inventory.on_hand - inventory.reserved

    async def get_inventory(self, variant_id: int) -> inventory_models.Inventory:
        inventory = await self.repository.get_by_variant_id(variant_id)
        if inventory is None:
            raise app.core.exceptions.ResourceNotFoundException(
                "Inventory does not exist."
            )
        return inventory

    async def adjust(
        self,
        variant_id: int,
        quantity_delta: int,
        reason: str,
        actor_user_id: int | None = None,
    ) -> inventory_models.Inventory:
        if quantity_delta == 0:
            raise app.core.exceptions.BadRequestException(
                "Adjustment quantity cannot be zero.",
                code="INVALID_ADJUSTMENT",
            )
        if not reason.strip():
            raise app.core.exceptions.BadRequestException(
                "Adjustment reason is required.",
                code="INVALID_ADJUSTMENT_REASON"
            )

        inventory = await self._get_or_create_locked(variant_id)
        new_on_hand = inventory.on_hand + quantity_delta

        if new_on_hand < 0:
            raise app.core.exceptions.ConflictException(
                message="On-hand quantity cannot be negative.",
                code="INVENTORY_NEGATIVE",
            )
        if new_on_hand < inventory.reserved:
            raise app.core.exceptions.ConflictException(
                message="On-hand quantity cannot be lower than reserved.",
                code="INVENTORY_BELOW_RESERVED",
            )

        inventory.on_hand = new_on_hand
        self._record_movement(
            inventory,
            inventory_models.MovementType.ADJUST_IN
            if quantity_delta > 0
            else inventory_models.MovementType.ADJUST_OUT,
            quantity_delta,
            reason=reason.strip(),
            actor_user_id=actor_user_id,
        )
        await self.session.commit()
        return inventory

    async def reserve(
        self,
        variant_id: int,
        quantity: int,
        order_id: int | None = None,
    ) -> inventory_models.Inventory:
        self._validate_quantity(quantity)
        inventory = await self.repository.get_for_update(variant_id)

        if (
            inventory is None
            or inventory.on_hand - inventory.reserved < quantity
        ):
            raise app.core.exceptions.ConflictException(
                message="Insufficient stock.",
                code="INSUFFICIENT_STOCK",
            )

        inventory.reserved += quantity
        self._record_movement(
            inventory,
            inventory_models.MovementType.RESERVE,
            quantity,
            order_id=order_id,
            reason="Order reservation",
        )
        await self.session.commit()
        return inventory

    async def release(
        self,
        variant_id: int,
        quantity: int,
        order_id: int | None = None,
    ) -> inventory_models.Inventory:
        self._validate_quantity(quantity)
        inventory = await self.repository.get_for_update(variant_id)

        if inventory is None or inventory.reserved < quantity:
            raise app.core.exceptions.ConflictException(
                message="Cannot release more than reserved.",
                code="INVALID_RELEASE",
            )

        inventory.reserved -= quantity
        self._record_movement(
            inventory,
            inventory_models.MovementType.RELEASE,
            -quantity,
            order_id=order_id,
            reason="Order reservation released",
        )
        await self.session.commit()
        return inventory

    async def confirm_sale(
        self,
        variant_id: int,
        quantity: int,
        order_id: int | None = None,
    ) -> inventory_models.Inventory:
        self._validate_quantity(quantity)
        inventory = await self.repository.get_for_update(variant_id)

        if (
            inventory is None
            or inventory.reserved < quantity
            or inventory.on_hand < quantity
        ):
            raise app.core.exceptions.ConflictException(
                message="Cannot confirm sale for the requested quantity.",
                code="INVALID_SALE",
            )

        inventory.on_hand -= quantity
        inventory.reserved -= quantity
        self._record_movement(
            inventory,
            inventory_models.MovementType.SALE,
            -quantity,
            order_id=order_id,
            reason="Payment confirmed",
        )
        await self.session.commit()
        return inventory

    async def _get_or_create_locked(self, variant_id: int) -> inventory_models.Inventory:
        inventory = await self.repository.get_for_update(variant_id)
        if inventory is not None:
            return inventory

        variant = await self.session.get(
            catalog_models.ProductVariant, variant_id
        )
        if variant is None:
            raise app.core.exceptions.ResourceNotFoundException(
                "Variant does not exist."
            )

        inventory = inventory_models.Inventory(
            variant_id=variant_id,
            on_hand=0,
            reserved=0,
        )
        self.repository.add(inventory)

        try:
            await self.session.flush()
        except sqlalchemy.exc.IntegrityError:
            # 并发首次入库：另一个事务已创建，回滚后重新加锁读取。
            await self.session.rollback()
            inventory = await self.repository.get_for_update(variant_id)
            if inventory is None:
                raise
        return inventory

    def _record_movement(
        self,
        inventory: inventory_models.Inventory,
        movement_type: inventory_models.MovementType,
        quantity_delta: int,
        *,
        order_id: int | None = None,
        reason: str | None = None,
        actor_user_id: int | None = None,
    ) -> None:
        self.repository.add_movement(
            inventory_models.InventoryMovement(
                inventory_id=inventory.id,
                order_id=order_id,
                movement_type=movement_type,
                quantity_delta=quantity_delta,
                on_hand_after=inventory.on_hand,
                reserved_after=inventory.reserved,
                reason=reason,
                actor_user_id=actor_user_id,
            )
        )

    @staticmethod
    def _validate_quantity(quantity: int) -> None:
        if quantity <= 0:
            raise app.core.exceptions.BadRequestException(
                "Quantity must be positive.",
                code="INVALID_QUANTITY",
            )

    async def list_inventory(
        self,
        page: int,
        page_size: int,
        variant_id: int | None = None,
    ) -> tuple[list[inventory_models.Inventory], int]:
        return await self.repository.list_inventory(page, page_size, variant_id)

    async def list_movements(
        self,
        page: int,
        page_size: int,
        variant_id: int | None = None,
    ) -> tuple[list[inventory_models.InventoryMovement], int]:
        inventory_id = None
        if variant_id is not None:
            inventory = await self.repository.get_by_variant_id(variant_id)
            if inventory is None:
                return [], 0
            inventory_id = inventory.id
            
        return await self.repository.list_movements(page, page_size, inventory_id)