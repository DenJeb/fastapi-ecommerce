import contextvars

request_id_context: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id",
    default=None,
)


def set_request_id(request_id: str) -> contextvars.Token:
    """设置当前请求 ID，并返回用于恢复上下文的 token"""
    return request_id_context.set(request_id)


def reset_request_id(token: contextvars.Token) -> None:
    """请求结束后恢复上下文"""
    request_id_context.reset(token)


def get_request_id() -> str | None:
    """获取当前请求 ID，不在请求上下文中时返回 None"""
    return request_id_context.get()