if __name__ == "__main__":
    import uvicorn
    import os
    uvicorn.run(
        "container_status_fastapi:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        workers=int(os.getenv("WORKERS", "1")),
    )