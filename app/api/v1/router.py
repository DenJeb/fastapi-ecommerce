import fastapi

import app.api.v1.endpoints.health

api_router = fastapi.APIRouter()

api_router.include_router(
    app.api.v1.endpoints.health.router,
)