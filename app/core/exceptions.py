class AppException(Exception):
    """异常基类，用于自定义应用程序异常"""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict | list | None = None,
        headers: dict[str, str] | None = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        self.headers = headers

        super().__init__(message)


class ResourceNotFoundException(AppException):
    """异常类，表示请求的资源未找到"""

    def __init__(self, message: str = "The requested resource was not found."):
        super().__init__(
            code="RESOURCE_NOT_FOUND",
            message=message,
            status_code=404
        )


class ConflictException(AppException):
    """异常类，表示请求的操作与现有数据冲突"""

    def __init__(
        self,
        message: str = "The requested operation conflicts with existing data.",
        code: str = "RESOURCE_CONFLICT",
    ):
        super().__init__(
            code=code,
            message=message,
            status_code=409,
        )


class UnauthorizedException(AppException):
    """未认证或凭据无效"""

    def __init__(
        self,
        message: str = "Authentication is required.",
        code: str = "UNAUTHORIZED",
    ):
        super().__init__(
            code=code,
            message=message,
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(AppException):
    """已认证但无权访问"""

    def __init__(
        self,
        message: str = "Permission denied",
        code: str = "FORBIDDEN"
    ):
        super().__init__(
            code=code,
            message=message,
            status_code=403,
        )


class BadRequestException(AppException):
    """请求本身不合法"""

    def __init__(
        self,
        message: str = "Bad request.",
        code: str = "BAD_REQUEST"
    ):
        super().__init__(code=code, message=message, status_code=400)