import pydantic


class RegisterRequest(pydantic.BaseModel):
    email: pydantic.EmailStr
    username: str = pydantic.Field(
        min_length=3,
        max_length=64,
        pattern=r"^[A-Za-z0-9_]+$",
    )
    password: str = pydantic.Field(
        min_length=8,
        max_length=128,
    )


class LoginRequest(pydantic.BaseModel):
    identifier: str = pydantic.Field(
        min_length=1,
        max_length=255,
        description="Email or username",
    )
    password: str = pydantic.Field(
        min_length=1,
        max_length=128,
    )


class TokenResponse(pydantic.BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RoleResponse(pydantic.BaseModel):
    name: str

    model_config = pydantic.ConfigDict(from_attributes=True)


class UserResponse(pydantic.BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    roles: list[RoleResponse]

    model_config = pydantic.ConfigDict(from_attributes=True)