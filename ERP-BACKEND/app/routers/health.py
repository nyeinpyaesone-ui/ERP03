from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from sqlalchemy import text
import os

router = APIRouter()


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_check():
    """Liveness probe - returns healthy if the application is running."""
    return {"status": "healthy", "check": "liveness"}


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness probe - returns healthy if all dependencies are available."""
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    overall_status = "healthy" if db_status == "healthy" else "degraded"
    return {
        "status": overall_status,
        "checks": {
            "database": db_status
        }
    }


@router.get("/health/startup", status_code=status.HTTP_200_OK)
async def startup_check():
    """Startup probe - returns healthy after application initialization."""
    return {"status": "healthy", "check": "startup"}


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Legacy health endpoint for backward compatibility."""
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "database": db_status
    }
