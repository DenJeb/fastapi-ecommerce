import decimal

import pydantic

import app.modules.catalog.models as catalog_models

class CategoryResponse(pydantic.BaseModel):
    id: int
    parent_id: int | None
    name: str
    slug: str
    is_active: bool

    model_config = pydantic.ConfigDict(from_attributes=True)


class CreateCategoryRequest(pydantic.BaseModel):
    name: str = pydantic.Field(
        min_length=1,
        max_length=100,
    )
    slug: str = pydantic.Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    parent_id: int | None = None
    is_active: bool = True

    model_config = pydantic.ConfigDict(str_strip_whitespace=True)


class UpdateCategoryRequest(pydantic.BaseModel):
    name: str | None = pydantic.Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    slug: str | None = pydantic.Field(
        default=None,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    parent_id: int | None = None
    is_active: bool | None = None

    model_config = pydantic.ConfigDict(str_strip_whitespace=True)

    @pydantic.model_validator(mode="after")
    def require_at_least_one_field(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")
        return self


class VariantResponse(pydantic.BaseModel):
    id: int
    product_id: int
    sku: str
    name: str
    price: decimal.Decimal
    is_active: bool

    model_config = pydantic.ConfigDict(from_attributes=True)

    @pydantic.field_serializer("price")
    def serialize_price(self, value: decimal.Decimal) -> str:
        # 金额用 str 返回
        return format(value, "f")


class ProductResponse(pydantic.BaseModel):
    id: int
    category_id: int
    name: str
    slug: str
    description: str | None
    status: catalog_models.ProductStatus
    variants: list[VariantResponse]

    model_config = pydantic.ConfigDict(from_attributes=True)


class ProductListResponse(pydantic.BaseModel):
    items: list[ProductResponse]
    page: int
    page_size: int
    total: int


class CreateProductRequest(pydantic.BaseModel):
    category_id: int
    name: str = pydantic.Field(
        min_length=1,
        max_length=200,
    )
    slug: str = pydantic.Field(
        min_length=1,
        max_length=200,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    description: str | None = None
    status: catalog_models.ProductStatus = catalog_models.ProductStatus.DRAFT

    model_config = pydantic.ConfigDict(str_strip_whitespace=True)


class UpdateProductRequest(pydantic.BaseModel):
    category_id: int | None = None
    name: str | None = pydantic.Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    slug: str | None = pydantic.Field(
        default=None,
        min_length=1,
        max_length=200,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    description: str | None = None
    status: catalog_models.ProductStatus | None = None

    model_config = pydantic.ConfigDict(str_strip_whitespace=True)

    @pydantic.model_validator(mode="after")
    def require_at_least_one_field(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")
        return self


class CreateVariantRequest(pydantic.BaseModel):
    sku: str = pydantic.Field(
        min_length=1,
        max_length=64,
    )
    name: str = pydantic.Field(
        min_length=1,
        max_length=100,
    )
    price: decimal.Decimal = pydantic.Field(
        ge=0,
        max_digits=12,
        decimal_places=2,
    )
    is_active: bool = True

    model_config = pydantic.ConfigDict(str_strip_whitespace=True)


class UpdateVariantRequest(pydantic.BaseModel):
    sku: str | None = pydantic.Field(
        default=None,
        min_length=1,
        max_length=64
    )
    name: str | None = pydantic.Field(
        default=None,
        min_length=1,
        max_length=100
    )
    price: decimal.Decimal | None = pydantic.Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=2,
    )
    is_active: bool | None = None

    model_config = pydantic.ConfigDict(str_strip_whitespace=True)

    @pydantic.model_validator(mode="after")
    def require_at_least_one_field(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")
        return self