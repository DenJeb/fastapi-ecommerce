import logging

import fastapi
import fastapi.exceptions
import starlette.exceptions

import app.api.v1.router
import app.core.config
import app.core.exception_handlers
import app.core.exceptions
import app.core.logging

app.core.logging.setup_logging(
    log_level=app.core.config.settings.log_level
)

logger = logging.getLogger(__name__)

application = fastapi.FastAPI(
    title=app.core.config.settings.app_name,
    version=app.core.config.settings.app_version,
    debug=app.core.config.settings.debug,
    description="This is the Saleor FastAPI Backend API.",
)

# App 异常处理器
application.add_exception_handler(
    app.core.exceptions.AppException,
    app.core.exception_handlers.app_exception_handler,
)

# HTTP 异常处理器
application.add_exception_handler(
    fastapi.HTTPException,
    app.core.exception_handlers.http_exception_handler,
)

# 验证异常处理器
application.add_exception_handler(
    fastapi.exceptions.RequestValidationError,
    app.core.exception_handlers.validation_exception_handler,
)

# 未预期异常处理器
application.add_exception_handler(
    Exception,
    app.core.exception_handlers.unexpected_exception_handler,
)

application.include_router(
    app.api.v1.router.api_router,
    prefix=app.core.config.settings.api_v1_prefix,
)


@application.get("/")
async def root():
    logger.info("Root endpoint accessed")

    return {
        "message": "Welcome to the Saleor FastAPI Backend!",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(application, host="0.0.0.0", port=8000)