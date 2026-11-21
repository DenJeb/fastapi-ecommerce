import datetime

import jwt
import pytest

import app.core.config
import app.core.security


def test_password_hash_is_not_plaintext():
    hashed = app.core.security.hash_password("secret123")

    assert hashed != "secret123"
    assert app.core.security.verify_password("secret123", hashed)


def test_verify_password_rejects_wrong_password():
    hashed = app.core.security.hash_password("secret123")

    assert app.core.security.verify_password("wrong", hashed) is False


def test_verify_password_rejects_malformed_hash():
    assert app.core.security.verify_password("secret123", "not-a-hash") is False


def test_same_password_gets_different_salts():
    first = app.core.security.hash_password("secret123")
    second = app.core.security.hash_password("secret123")

    assert first != second


def test_access_token_round_trip():
    token = app.core.security.create_access_token("42")
    payload = app.core.security.decode_access_token(token)

    assert payload["sub"] == "42"
    assert payload["type"] == "access"
    assert "iat" in payload
    assert "exp" in payload


def test_expired_access_token_is_rejected():
    token = app.core.security.create_access_token(
        "42",
        expires_delta=datetime.timedelta(seconds=-1),
    )

    with pytest.raises(app.core.security.InvalidTokenError):
        app.core.security.decode_access_token(token)


def test_invalid_access_token_is_rejected():
    with pytest.raises(app.core.security.InvalidTokenError):
        app.core.security.decode_access_token("not-a-jwt")


def test_non_access_token_is_rejected():
    now = datetime.datetime.now(datetime.timezone.utc)
    token = jwt.encode(
        {
            "sub": "42",
            "type": "refresh",
            "iat": now,
            "exp": now + datetime.timedelta(minutes=5),
        },
        app.core.config.settings.jwt_secret_key.get_secret_value(),
        algorithm=app.core.config.settings.jwt_algorithm,
    )

    with pytest.raises(app.core.security.InvalidTokenError):
        app.core.security.decode_access_token(token)