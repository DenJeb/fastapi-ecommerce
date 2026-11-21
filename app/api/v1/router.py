import fastapi

import app.modules.auth.router
import app.modules.health.router

api_router = fastapi.APIRouter()

api_router.include_router(
    app.modules.auth.router.router,
)
api_router.include_router(
    app.modules.health.router.router,
)