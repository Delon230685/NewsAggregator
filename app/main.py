from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.simple_endpoints import router
from app.database import db
from app.config import config

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
async def root():
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
async def startup_event():
    # Создание таблиц в БД
    db.create_tables()
    print(f"{config.APP_NAME} started successfully!")
    print(f"Swagger UI: http://localhost:8000/docs")
    print(f"ReDoc: http://localhost:8000/redoc")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )