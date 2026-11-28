import datetime
import decimal

import pydantic

import app.modules.orders.models as order_models


class OrderItemResponse(pydantic.BaseModel):
    id: int
    variant_id: int | None
    product_name: str
    sku: str
    variant_name: str
    unit_price: decimal.Decimal
    quantity: int
    line_total: decimal.Decimal

    model_config = pydantic.ConfigDict(from_attributes=True)

    @pydantic.field_serializer("unit_price", "line_total")
    def serialize_amount(self, value: decimal.Decimal) -> str:
        return format(value, "f")


class OrderResponse(pydantic.BaseModel):
    id: int
    order_no: str
    status: order_models.OrderStatus
    currency: str
    subtotal: decimal.Decimal
    discount_total: decimal.Decimal
    total_amount: decimal.Decimal
    created_at: datetime.datetime
    items: list[OrderItemResponse]

    model_config = pydantic.ConfigDict(from_attributes=True)

    @pydantic.field_serializer("subtotal", "discount_total", "total_amount")
    def serialize_amount(self, value: decimal.Decimal) -> str:
        return format(value, "f")