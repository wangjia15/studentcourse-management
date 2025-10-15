from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import api_router
from app.db.database import engine
from app.models import user, course, grade, auth_log
from app.middleware.auth import (
    AuthenticationMiddleware,
    LoggingMiddleware,
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Chinese University Grade Management System API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up security middleware (order matters)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
app.add_middleware(LoggingMiddleware)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware (after CORS)
app.add_middleware(
    AuthenticationMiddleware,
    exclude_paths=[
        "/",
        f"{settings.API_V1_STR}/auth/login",
        f"{settings.API_V1_STR}/auth/register",
        f"{settings.API_V1_STR}/auth/password-reset",
        "/docs",
        "/openapi.json",
        "/favicon.ico",
        "/static",
        "/health",
    ]
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {
        "message": "Chinese University Grade Management System API",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "grade-management-backend"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
