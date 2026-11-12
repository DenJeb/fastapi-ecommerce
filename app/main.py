import logging

import fastapi
import fastapi.exceptions

import app.api.v1.router
import app.core.config
import app.core.exception_handlers
import app.core.exceptions
import app.core.logging
import app.core.middleware

logger = logging.getLogger(__name__)

application = fastapi.FastAPI(
    title=app.core.config.settings.app_name,
    version=app.core.config.settings.app_version,
    debug=app.core.config.settings.debug,
    description="This is the Saleor FastAPI Backend API.",
)

# 初始化日志
app.core.logging.setup_logging(
    log_level=app.core.config.settings.log_level
)

# 注册异常处理
app.core.exception_handlers.register_exception_handlers(application)

# 注册中间件
app.core.middleware.register_middlewares(application)

# 注册 API 路由
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