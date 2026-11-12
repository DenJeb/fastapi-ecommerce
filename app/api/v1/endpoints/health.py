import fastapi

router = fastapi.APIRouter()


@router.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "OK",
    }