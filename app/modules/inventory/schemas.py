import datetime

import pydantic

import app.modules.inventory.models as inventory_models


class InventoryResponse(pydantic.BaseModel):
    id: int
    variant_id: int
    on_hand: int
    reserved: int
    available: int

    model_config = pydantic.ConfigDict(from_attributes=True)


class InventoryAdjustmentRequest(pydantic.BaseModel):
    quantity_delta: int
    reason: str = pydantic.Field(min_length=1, max_length=255)

    model_config = pydantic.ConfigDict(str_strip_whitespace=True)

    @pydantic.field_validator("quantity_delta")
    @classmethod
    def quantity_delta_must_not_be_zero(cls, value: int) -> int:
        if value == 0:
            raise ValueError("quantity_delta cannot be zero.")
        return value


class InventoryListResponse(pydantic.BaseModel):
    items: list[InventoryResponse]
    page: int
    page_size: int
    total: int


class InventoryMovementResponse(pydantic.BaseModel):
    id: int
    inventory_id: int
    order_id: int | None
    movement_type: inventory_models.MovementType
    quantity_delta: int
    on_hand_after: int
    reserved_after: int
    reason: str | None
    actor_user_id: int | None
    created_at: datetime.datetime

    model_config = pydantic.ConfigDict(from_attributes=True)


class InventoryMovementListResponse(pydantic.BaseModel):
    items: list[InventoryMovementResponse]
    page: int
    page_size: int
    total: int