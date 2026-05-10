from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.simple_endpoints import router
from app.database import db
from app.config import config
from app.logger import logger

app = FastAPI(
    title=config.APP_NAME + " - API Documentation",
    description="AI-powered Telegram news bot with automatic post generation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root() -> dict[str, str | dict[str, str]]:
    """Корневой эндпоинт с информацией о доступных API"""
    return {
        "message": f"Welcome to {config.APP_NAME}",
        "docs": "/docs",
        "endpoints": {
            "sources": "/api/sources/",
            "keywords": "/api/keywords/",
            "news": "/api/news/",
            "posts": "/api/posts/",
            "generate": "/api/generate/",
            "stats": "/api/stats/",
            "health": "/api/health",
            "dashboard": "/api/dashboard"
        },
        "status": "running"
    }


@app.on_event("startup")
async def startup_event() -> None:
    """Действия при запуске приложения"""
    db.create_tables()
    logger.info(f"{config.APP_NAME} started successfully!")
    logger.info(f"Swagger UI: http://localhost:8000/docs")
    logger.info(f"ReDoc: http://localhost:8000/redoc")

    if config.DEBUG:
        logger.debug("Running in DEBUG mode")
        openai_config = config.get_openai_config()
        if openai_config["is_configured"]:
            logger.info(f"OpenAI configured with model: {openai_config['model']}")
        else:
            logger.warning("OpenAI API key not configured, using fallback generation")

        telegram_config = config.get_telegram_config()
        if telegram_config["is_configured"]:
            logger.info("Telegram bot configured")
        else:
            logger.warning("Telegram not configured, publishing disabled")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Действия при остановке приложения"""
    logger.info(f"{config.APP_NAME} shutting down...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.DEBUG
    )