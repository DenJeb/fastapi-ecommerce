import dataclasses
import decimal
import uuid

import sqlalchemy
import sqlalchemy.exc
import sqlalchemy.ext.asyncio

import app.core.exceptions
import app.modules.cart.models as cart_models
import app.modules.cart.service
import app.modules.catalog.models as catalog_models
import app.modules.checkout.schemas as checkout_schemas
import app.modules.inventory.service
import app.modules.orders.models as order_models
import app.modules.orders.repository


@dataclasses.dataclass
class CheckoutLine:
    variant_id: int
    sku: str
    product_name: str
    variant_name: str
    unit_price: decimal.Decimal
    quantity: int
    line_total: decimal.Decimal


class CheckoutService:
    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession):
        self.session = session
        self.cart_service = app.modules.cart.service.CartService(session)
        self.inventory_service = app.modules.inventory.service.InventoryService(session)
        self.order_repository = app.modules.orders.repository.OrderRepository(session)

    async def preview(self, user_id: int) -> checkout_schemas.CheckoutPreviewResponse:
        cart = await self.cart_service.get_or_create(user_id)
        lines = await self._load_lines(cart)

        items = []
        for line in lines:
            available = await self.inventory_service.get_available(line.variant_id)
            if available < line.quantity:
                raise app.core.exceptions.ConflictException(
                    message=(
                        f"Insufficient stock for variant {line.variant_id}."
                    ),
                    code="INSUFFICIENT_STOCK",
                )
            items.append(
                checkout_schemas.CheckoutItemResponse(
                    variant_id=line.variant_id,
                    sku=line.sku,
                    product_name=line.product_name,
                    variant_name=line.variant_name,
                    unit_price=line.unit_price,
                    quantity=line.quantity,
                    line_total=line.line_total,
                    available=available,
                )
            )

        subtotal = self._subtotal(lines)
        return checkout_schemas.CheckoutPreviewResponse(
            items=items,
            subtotal=subtotal,
            discount_total=decimal.Decimal("0.00"),
            total_amount=subtotal,
            currency="CNY",
        )

    async def create_order(
        self,
        user_id: int,
        idempotency_key: str | None,
    ) -> tuple[order_models.Order, bool]:
        key = idempotency_key.strip() if idempotency_key else None
        if key:
            existing = await self.order_repository.get_by_idempotency_key(user_id, key)
            if existing is not None:
                return existing, False

        cart = await self.cart_service.get_or_create(user_id)
        lines = await self._load_lines(cart)
        subtotal = self._subtotal(lines)
        discount_total = decimal.Decimal("0.00")
        total_amount = subtotal - discount_total

        order = order_models.Order(
            order_no=self._generate_order_no(),
            user_id=user_id,
            status=order_models.OrderStatus.PENDING_PAYMENT,
            currency="CNY",
            subtotal=subtotal,
            discount_total=discount_total,
            total_amount=total_amount,
            idempotency_key=key,
            items=[
                order_models.OrderItem(
                    variant_id=line.variant_id,
                    product_name_snapshot=line.product_name,
                    sku_snapshot=line.sku,
                    variant_name_snapshot=line.variant_name,
                    unit_price=line.unit_price,
                    quantity=line.quantity,
                    line_total=line.line_total,
                )
                for line in lines
            ],
            events=[
                order_models.OrderEvent(
                    from_status=None,
                    to_status=order_models.OrderStatus.PENDING_PAYMENT,
                    actor_user_id=user_id,
                    reason="Order created",
                )
            ],
        )
        self.order_repository.add(order)
        await self.session.flush()

        try:
            for line in lines:
                await self.inventory_service.reserve(
                    line.variant_id,
                    line.quantity,
                    order_id=order.id,
                    commit=False,
                )
        except Exception:
            await self.session.rollback()
            raise

        cart.items.clear()

        try:
            await self.session.commit()
        except sqlalchemy.exc.IntegrityError:
            await self.session.rollback()
            if key:
                existing = await self.order_repository.get_by_idempotency_key(
                    user_id, key
                )
                if existing is not None:
                    return existing, False
            raise

        return order, True

    async def _load_lines(self, cart: cart_models.Cart) -> list[CheckoutLine]:
        if not cart.items:
            raise app.core.exceptions.BadRequestException(
                "Cart is empty.",
                code="CART_EMPTY",
            )

        product_ids = {item.variant.product_id for item in cart.items}
        result = await self.session.execute(
            sqlalchemy.select(catalog_models.Product).where(
                catalog_models.Product.id.in_(product_ids)
            )
        )
        products = {
            product.id: product
            for product in result.scalars().all()
        }

        lines = []
        for item in cart.items:
            variant = item.variant
            product = products.get(variant.product_id)
            if (
                product is None
                or product.status != catalog_models.ProductStatus.ACTIVE
                or not variant.is_active
            ):
                raise app.core.exceptions.ConflictException(
                    message=f"Item {variant.sku} is not available.",
                    code="ITEM_NOT_AVAILABLE",
                )

            lines.append(
                CheckoutLine(
                    variant_id=variant.id,
                    sku=variant.sku,
                    product_name=product.name,
                    variant_name=variant.name,
                    unit_price=variant.price,
                    quantity=item.quantity,
                    line_total=variant.price * item.quantity,
                )
            )

        # 固定加锁顺序，降低多 SKU 并发下单时互相等待的概率。
        lines.sort(key=lambda line: line.variant_id)
        return lines

    @staticmethod
    def _subtotal(lines: list[CheckoutLine]) -> decimal.Decimal:
        return sum(
            (line.line_total for line in lines),
            decimal.Decimal("0.00"),
        ).quantize(decimal.Decimal("0.01"))

    @staticmethod
    def _generate_order_no() -> str:
        return f"ORD-{uuid.uuid4().hex[:28]}"
        