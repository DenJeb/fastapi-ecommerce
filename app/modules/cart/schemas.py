import decimal

import pydantic


class CartItemResponse(pydantic.BaseModel):
    id: int
    variant_id: int
    sku: str
    name: str
    unit_price: decimal.Decimal
    quantity: int
    line_total: decimal.Decimal

    model_config = pydantic.ConfigDict(from_attributes=True)

    @pydantic.field_serializer("unit_price", "line_total")
    def serialize_amount(self, value: decimal.Decimal) -> str:
        return format(value, "f")


class CartResponse(pydantic.BaseModel):
    id: int
    items: list[CartItemResponse]
    subtotal: decimal.Decimal
    total_quantity: int

    model_config = pydantic.ConfigDict(from_attributes=True)

    @pydantic.field_serializer("subtotal")
    def serialize_subtotal(self, value: decimal.Decimal) -> str:
        return format(value, "f")


class AddCartItemRequest(pydantic.BaseModel):
    variant_id: int
    quantity: int = pydantic.Field(ge=1)


class UpdateCartItemRequest(pydantic.BaseModel):
    quantity: int = pydantic.Field(ge=1)