import sqlalchemy.exc
import sqlalchemy.ext.asyncio

import app.core.exceptions
import app.modules.cart.models as cart_models
import app.modules.cart.repository


class CartService:
    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession):
        self.session = session
        self.repository = app.modules.cart.repository.CartRepository(session)

    async def get_or_create(self, user_id: int) -> cart_models.Cart:
        cart = await self.repository.get_by_user_id(user_id)
        if cart is not None:
            return cart

        cart = cart_models.Cart(user_id=user_id, items=[])
        self.repository.add(cart)

        try:
            await self.session.commit()
        except sqlalchemy.exc.IntegrityError:
            # 首次并发访问，另一个请求已创建购物车
            await self.session.rollback()
            cart = await self.repository.get_by_user_id(user_id)
            if cart is None:
                raise
        return cart

    async def add_item(
        self,
        user_id: int,
        variant_id: int,
        quantity: int,
    ) -> cart_models.Cart:
        self._validate_quantity(quantity)

        variant = await self.repository.get_available_variant(variant_id)
        if variant is None:
            raise app.core.exceptions.ResourceNotFoundException(
                "Variant is not available."
            )

        cart = await self.get_or_create(user_id)

        for item in cart.items:
            if item.variant_id == variant_id:
                item.quantity += quantity
                break
        else:
            cart.items.append(
                cart_models.CartItem(
                    variant_id=variant_id,
                    variant=variant,
                    quantity=quantity,
                )
            )

        await self.session.commit()
        return cart

    async def update_item(
        self,
        user_id: int,
        item_id: int,
        quantity: int,
    ) -> cart_models.Cart:
        self._validate_quantity(quantity)

        cart = await self.get_or_create(user_id)
        item = next(
            (cart_item for cart_item in cart.items if cart_item.id == item_id),
            None,
        )
        if item is None:
            raise app.core.exceptions.ResourceNotFoundException(
                "Cart item does not exist."
            )

        item.quantity = quantity
        await self.session.commit()
        return cart

    async def remove_item(
        self, user_id: int, item_id: int
    ) -> cart_models.Cart:
        cart = await self.get_or_create(user_id)
        item = next(
            (cart_item for cart_item in cart.items if cart_item.id == item_id),
            None,
        )
        if item is None:
            raise app.core.exceptions.ResourceNotFoundException(
                "Cart item does not exist."
            )

        cart.items.remove(item)
        await self.session.commit()
        return cart

    @staticmethod
    def _validate_quantity(quantity: int) -> None:
        if quantity <= 0:
            raise app.core.exceptions.BadRequestException(
                "Quantity must be positive.",
                code="INVALID_QUANTITY",
            )