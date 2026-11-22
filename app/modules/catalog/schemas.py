import pydantic


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