import os
from datetime import datetime

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

app = FastAPI(
    title="Time Server API",
    description="Простое API для получения текущего времени сервера",
    version="1.0.0",
)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "Добро пожаловать в Time Server API",
        "docs": "/docs",
    }


@app.get("/time")
async def get_current_time() -> dict[str, str | float | None]:
    now = datetime.now()
    return {
        "current_time": now.isoformat(),
        "timestamp": now.timestamp(),
        "formatted_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": str(now.astimezone().tzinfo),
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"}
    uvicorn.run("main:app", host=host, port=port, reload=debug)
