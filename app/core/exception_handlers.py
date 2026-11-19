import logging

import fastapi
import fastapi.encoders
import fastapi.exceptions
import fastapi.responses
import starlette.exceptions

import app.core.exceptions

logger = logging.getLogger(__name__)


def _error_response(
    request: fastapi.Request,
    status_code: int,
    code: str,
    message: str,
    details: dict | list | None = None,
    headers: dict[str, str] | None = None,
) -> fastapi.responses.JSONResponse:
    """按 05-api-design.md 的统一结构返回错误"""
    request_id = getattr(request.state, "request_id", None)

    response_headers = dict(headers) if headers else {}
    if request_id:
        response_headers.setdefault("X-Request-ID", request_id)

    return fastapi.responses.JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "request_id": request_id,
            }
        },
        headers=response_headers,
    )


async def app_exception_handler(
    request: fastapi.Request,
    exc: app.core.exceptions.AppException,
):
    """处理自定义应用程序异常的异常处理器"""
    return _error_response(
        request=request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )


async def http_exception_handler(
    request: fastapi.Request,
    exc: starlette.exceptions.HTTPException,
):
    """处理HTTP异常的异常处理器"""
    return _error_response(
        request=request,
        status_code=exc.status_code,
        code="HTTP_ERROR",
        message=str(exc.detail),
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: fastapi.Request,
    exc: fastapi.exceptions.RequestValidationError,
):
    """处理验证异常的异常处理器"""
    return _error_response(
        request=request,
        status_code=422,
        code="VALIDATION_ERROR",
        message="Request validation failed.",
        details=fastapi.encoders.jsonable_encoder(exc.errors()),
    )


async def unexpected_exception_handler(
    request: fastapi.Request,
    exc: Exception,
):
    """处理未预期异常的异常处理器"""
    logger.exception(
        "Unexpected exception occurred: %s %s",
        request.method,
        request.url.path,
    )

    return _error_response(
        request=request,
        status_code=500,
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred.",
    )


def register_exception_handlers(
    application: fastapi.FastAPI
) -> None:
    """注册异常处理器"""
    # App 异常处理器
    application.add_exception_handler(
        app.core.exceptions.AppException,
        app_exception_handler,
    )

    # HTTP 异常处理器
    application.add_exception_handler(
        starlette.exceptions.HTTPException,
        http_exception_handler,
    )

    # 验证异常处理器
    application.add_exception_handler(
        fastapi.exceptions.RequestValidationError,
        validation_exception_handler,
    )

    # 未预期异常处理器
    application.add_exception_handler(
        Exception,
        unexpected_exception_handler,
    )