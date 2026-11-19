import logging
import re
import time
import typing
import uuid

import fastapi
import starlette.requests
import starlette.responses

import app.core.request_context

logger = logging.getLogger("app.request")

_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def _resolve_request_id(request: starlette.requests.Request) -> str:
    """优先使用客户端传入的合法请求 ID，否则生成新的 ID"""
    incoming = request.headers.get("X-Request-ID", "").strip()
    if _REQUEST_ID_PATTERN.fullmatch(incoming):
        return incoming
    return uuid.uuid4().hex


def register_middlewares(application: fastapi.FastAPI) -> None:
    @application.middleware("http")
    async def log_requests(
        request: starlette.requests.Request,
        call_next: typing.Callable,
    ) -> starlette.responses.Response:
        request_id = _resolve_request_id(request)
        request.state.request_id = request_id
        token = app.core.request_context.set_request_id(request_id)
        
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration = (time.perf_counter() - start_time) * 1000

            logger.exception(
                "Request failed: %s %s | %.2f ms",
                request.method,
                request.url.path,
                duration,
            )
            raise
        else:
            duration = (time.perf_counter() - start_time) * 1000
            logger.info(
                "%s %s | Status: %s | %.2f ms",
                request.method,
                request.url.path,
                response.status_code,
                duration,
            )
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            app.core.request_context.reset_request_id(token)