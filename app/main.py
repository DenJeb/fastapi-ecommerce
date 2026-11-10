import fastapi

from app.core import config


app = fastapi.FastAPI(
    title=config.settings.app_name,
    version=config.settings.app_version,
    debug=config.settings.debug,
    description="This is the Saleor FastAPI Backend API.",
)


@app.get("/")
async def root():
    return {
        "message": "Welcome to the Saleor FastAPI Backend!",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "OK",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)