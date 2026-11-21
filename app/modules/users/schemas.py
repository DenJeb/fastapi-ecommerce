import pydantic


class UpdateUserRequest(pydantic.BaseModel):
    email: pydantic.EmailStr | None = None
    username: str | None = pydantic.Field(
        default=None,
        min_length=3,
        max_length=64,
        pattern="^[A-Za-z0-9_]+$"
    )

    @pydantic.model_validator(mode="after")
    def require_at_least_one_field(self):
        if self.email is None and self.username is None:
            raise ValueError("At least one field must be provided.")
        return self