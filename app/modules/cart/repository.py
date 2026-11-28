import sqlalchemy
import sqlalchemy.ext.asyncio

import app.modules.cart.models as cart_models
import app.modules.catalog.models as catalog_models


class CartRepository:
    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: int) -> cart_models.Cart | None:
        result = await self.session.execute(
            sqlalchemy.select(cart_models.Cart).where(
                cart_models.Cart.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_available_variant(self, variant_id: int) -> catalog_models.ProductVariant | None:
        result = await self.session.execute(
            sqlalchemy.select(catalog_models.ProductVariant)
            .join(
                catalog_models.Product,
                catalog_models.ProductVariant.product_id == catalog_models.Product.id,
            )
            .where(
                catalog_models.ProductVariant.id == variant_id,
                catalog_models.ProductVariant.is_active.is_(True),
                catalog_models.Product.status == catalog_models.ProductStatus.ACTIVE,
            )
        )
        return result.scalar_one_or_none()

    def add(self, cart: cart_models.Cart) -> None:
        self.session.add(cart)