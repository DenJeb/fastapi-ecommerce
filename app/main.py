import fastapi

app = fastapi.FastAPI(
    title="Saleor FastAPI Backend",
    description="A learning-oriented e-commerce backend API.",
    version="0.1.0",
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