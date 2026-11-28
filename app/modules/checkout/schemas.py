import decimal

import pydantic


class CheckoutItemResponse(pydantic.BaseModel):
    variant_id: int
    sku: str
    product_name: str
    variant_name: str
    unit_price: decimal.Decimal
    quantity: int
    line_total: decimal.Decimal
    available: int

    @pydantic.field_serializer("unit_price", "line_total")
    def serialize_amount(self, value: decimal.Decimal) -> str:
        return format(value, "f")


class CheckoutPreviewResponse(pydantic.BaseModel):
    items: list[CheckoutItemResponse]
    subtotal: decimal.Decimal
    discount_total: decimal.Decimal
    total_amount: decimal.Decimal
    currency: str = "CNY"

    @pydantic.field_serializer("subtotal", "discount_total", "total_amount")
    def serialize_amount(self, value: decimal.Decimal) -> str:
        return format(value, "f")