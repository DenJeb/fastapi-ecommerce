import datetime
import typing

import jwt
import pwdlib
import pwdlib.exceptions

import app.core.config


class InvalidTokenError(Exception):
    """JWT 无效、过期或不正确"""


# 避免相同密码获得相同哈希
_password_hasher = pwdlib.PasswordHash.recommended()


def hash_password(password: str) -> str:
    """生成哈希密码，返回值直接存入 users.password_hash"""
    return _password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验密码，哈希损坏或算法不可用按验证失败处理"""
    try:
        return _password_hasher.verify(plain_password, hashed_password)
    except pwdlib.exceptions.PwdlibError:
        return False


def create_access_token(
    subject: str,
    expires_delta: datetime.timedelta | None = None,
) -> str:
    """创建 access token"""
    now = datetime.datetime.now(datetime.timezone.utc)
    lifetime = (
        expires_delta
        if expires_delta is not None
        else datetime.timedelta(
            minutes=app.core.config.settings.access_token_expire_minutes
        )
    )
    payload = {
        "sub": subject,
        "type": "access",
        "iat": now,
        "exp": now + lifetime,
    }
    return jwt.encode(
        payload,
        app.core.config.settings.jwt_secret_key.get_secret_value(),
        algorithm=app.core.config.settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict[str, typing.Any]:
    """解析并校验 access token"""
    try:
        payload = jwt.decode(
            token,
            app.core.config.settings.jwt_secret_key.get_secret_value(),
            algorithms=[app.core.config.settings.jwt_algorithm],
            options={"require": ["exp", "iat", "sub", "type"]}
        )
    except jwt.PyJWTError as exc:
        raise InvalidTokenError("Token is invalid or expired.") from exc

    if payload.get("type") != "access":
        raise InvalidTokenError("Token is invalid.")

    return payload