import fastapi

import app.modules.auth.router
import app.modules.catalog.router
import app.modules.health.router
import app.modules.inventory.router
import app.modules.users.router

api_router = fastapi.APIRouter()

api_router.include_router(
    app.modules.auth.router.router,
)
api_router.include_router(
    app.modules.catalog.router.router,
)
api_router.include_router(
    app.modules.health.router.router,
)
api_router.include_router(
    app.modules.inventory.router.router,
)
api_router.include_router(
    app.modules.users.router.router,
)