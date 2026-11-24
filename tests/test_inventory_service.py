import asyncio
import decimal

import pytest
import sqlalchemy
import sqlalchemy.ext.asyncio
import sqlalchemy.pool

import app.core.exceptions
import app.db.session
import app.modules.catalog.models as catalog_models
import app.modules.inventory.models as inventory_models
import app.modules.inventory.service as inventory_service


async def _create_variant(factory) -> int:
    async with factory() as session:
        category = catalog_models.Category(name="Books", slug="books")
        session.add(category)
        await session.flush()

        product = catalog_models.Product(
            category_id=category.id,
            name="Book",
            slug="book",
            status=catalog_models.ProductStatus.ACTIVE,
        )
        session.add(product)
        await session.flush()

        variant = catalog_models.ProductVariant(
            product_id=product.id,
            sku="SKU-1",
            name="Default",
            price=decimal.Decimal("10.00"),
        )
        session.add(variant)
        await session.commit()
        return variant.id


def _run(action):
    async def main():
        engine = sqlalchemy.ext.asyncio.create_async_engine(
            app.db.session.database_url,
            poolclass=sqlalchemy.pool.NullPool,
        )
        factory = sqlalchemy.ext.asyncio.async_sessionmaker(
            engine,
            expire_on_commit=False,
        )
        try:
            return await action(factory)
        finally:
            await engine.dispose()

    return asyncio.run(main())


def test_adjust_records_movement():
    async def scenario(factory):
        variant_id = await _create_variant(factory)

        async with factory() as session:
            service = inventory_service.InventoryService(session)
            inventory = await service.adjust(
                variant_id, 5, reason="Initial stock"
            )
            assert inventory.on_hand == 5
            assert inventory.reserved == 0

        async with factory() as session:
            movement = await session.scalar(
                sqlalchemy.select(inventory_models.InventoryMovement)
            )
            assert movement is not None
            assert (
                movement.movement_type
                == inventory_models.MovementType.ADJUST_IN
            )
            assert movement.quantity_delta == 5
            assert movement.on_hand_after == 5
            assert movement.reserved_after == 0

    _run(scenario)


def test_adjust_below_reserved_is_rejected():
    async def scenario(factory):
        variant_id = await _create_variant(factory)

        async with factory() as session:
            service = inventory_service.InventoryService(session)
            await service.adjust(variant_id, 5, reason="Initial stock")
            await service.reserve(variant_id, 3)

        async with factory() as session:
            service = inventory_service.InventoryService(session)
            with pytest.raises(
                app.core.exceptions.ConflictException
            ) as exc_info:
                await service.adjust(variant_id, -3, reason="Damage")
            assert exc_info.value.code == "INVENTORY_BELOW_RESERVED"

    _run(scenario)


def test_reserve_prevents_overselling():
    async def scenario(factory):
        variant_id = await _create_variant(factory)

        async with factory() as session:
            service = inventory_service.InventoryService(session)
            await service.adjust(variant_id, 2, reason="Initial stock")

        async with factory() as session:
            service = inventory_service.InventoryService(session)
            with pytest.raises(
                app.core.exceptions.ConflictException
            ) as exc_info:
                await service.reserve(variant_id, 3)
            assert exc_info.value.code == "INSUFFICIENT_STOCK"

        async with factory() as session:
            service = inventory_service.InventoryService(session)
            await service.reserve(variant_id, 2)
            assert await service.get_available(variant_id) == 0

    _run(scenario)


def test_release_restores_available():
    async def scenario(factory):
        variant_id = await _create_variant(factory)

        async with factory() as session:
            service = inventory_service.InventoryService(session)
            await service.adjust(variant_id, 5, reason="Initial stock")
            await service.reserve(variant_id, 3)
            inventory = await service.release(variant_id, 2)

            assert inventory.reserved == 1
            assert await service.get_available(variant_id) == 4

    _run(scenario)


def test_confirm_sale_deducts_on_hand_and_reserved():
    async def scenario(factory):
        variant_id = await _create_variant(factory)

        async with factory() as session:
            service = inventory_service.InventoryService(session)
            await service.adjust(variant_id, 5, reason="Initial stock")
            await service.reserve(variant_id, 3)
            inventory = await service.confirm_sale(variant_id, 3)

            assert inventory.on_hand == 2
            assert inventory.reserved == 0

    _run(scenario)


def test_reserve_is_atomic_under_concurrency():
    async def scenario(factory):
        variant_id = await _create_variant(factory)

        async with factory() as session:
            service = inventory_service.InventoryService(session)
            await service.adjust(variant_id, 1, reason="Initial stock")

        async def reserve_once():
            async with factory() as session:
                service = inventory_service.InventoryService(session)
                try:
                    await service.reserve(variant_id, 1)
                    return "ok"
                except app.core.exceptions.AppException:
                    return "conflict"

        results = await asyncio.gather(reserve_once(), reserve_once())

        assert sorted(results) == ["conflict", "ok"]

        async with factory() as session:
            service = inventory_service.InventoryService(session)
            inventory = await service.get_inventory(variant_id)
            assert inventory.on_hand == 1
            assert inventory.reserved == 1

    _run(scenario)