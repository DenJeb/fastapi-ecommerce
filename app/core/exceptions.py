class AppException(Exception):
    """异常基类，用于自定义应用程序异常"""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict | list | None = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details

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

    def __init__(self, message: str = "The requested operation conflicts with existing data."):
        super().__init__(
            code="RESOURCE_CONFLICT",
            message=message,
            status_code=409
        )