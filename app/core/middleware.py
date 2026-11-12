import logging
import time
import typing

import fastapi
import starlette.requests
import starlette.responses

logger = logging.getLogger("app.request")


def register_middlewares(application: fastapi.FastAPI) -> None:
    @application.middleware("http")
    async def log_requests(
        request: starlette.requests.Request,
        call_next: typing.Callable,
    ) -> starlette.responses.Response:
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration = (time.perf_counter() - start_time) * 1000

            logger.exception(
                "Request falied: %s %s | %.2f ms",
                request.method,
                request.url.path,
                duration,
            )
            raise

        duration = (time.perf_counter() - start_time) * 1000

        logger.info(
            "%s %s | Status: %s | %.2f ms",
            request.method,
            request.url.path,
            response.status_code,
            duration,
        )

        return response
    