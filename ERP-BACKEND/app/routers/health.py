from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from sqlalchemy import text

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "version": "1.0.0",
        "database": db_status
    }

@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_probe():
    """Kubernetes liveness probe - is the application running?"""
    return {"status": "alive"}

@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_probe(db: AsyncSession = Depends(get_db)):
    """Kubernetes readiness probe - is the application ready to serve traffic?"""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return {"status": "not_ready", "database": "disconnected"}

@router.get("/health/startup", status_code=status.HTTP_200_OK)
async def startup_probe():
    """Kubernetes startup probe - has the application finished initialization?"""
    return {"status": "started"}
