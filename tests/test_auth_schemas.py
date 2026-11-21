import pydantic
import pytest

import app.modules.auth.schemas


def test_register_request_accepts_valid_payload():
    payload = app.modules.auth.schemas.RegisterRequest(
        email="user@example.com",
        username="user_1",
        password="password123",
    )

    assert payload.email == "user@example.com"
    assert payload.username == "user_1"


def test_register_request_rejects_invalid_email():
    with pytest.raises(pydantic.ValidationError):
        app.modules.auth.schemas.RegisterRequest(
            email="not-an-email",
            username="user_1",
            password="password123",
        )


def test_register_request_rejects_invalid_password():
    with pytest.raises(pydantic.ValidationError):
        app.modules.auth.schemas.RegisterRequest(
            email="user@example.com",
            username="user_1",
            password="short",
        )


def test_register_request_rejects_invalid_username():
    with pytest.raises(pydantic.ValidationError):
        app.modules.auth.schemas.RegisterRequest(
            email="user@example.com",
            username="uesr-name",
            password="password123",
        )