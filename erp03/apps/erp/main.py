"""
ERP03 v1.0.0 - Core Module Initialization
FastAPI application with domain routers, middleware, and lifespan management
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from apps.erp.core.config_manager import settings
from apps.erp.core.logging_setup import setup_logging, logger
from apps.erp.core.database_session import init_db, close_db
from apps.erp.modules.finance.apis.router import router as finance_router

# Import other domain routers (HCM placeholder for now)
from apps.erp.core.rbac_engine import rbac_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    # Startup
    logger.info("ERP03 Core Starting...")
    setup_logging()
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database URL: {settings.DATABASE_URL[:30]}...")
    
    # Initialize database tables
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    # Initialize RBAC with default roles
    logger.info(f"Loaded {len(rbac_engine.roles)} RBAC roles")
    
    yield
    
    # Shutdown
    logger.info("ERP03 Core Shutting down...")
    await close_db()
    logger.info("Database connections closed")


app = FastAPI(
    title="ERP03 Core",
    version="1.0.0",
    description="Enterprise Resource Planning System - Core API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS - Secure configuration with specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register Domain Routers
app.include_router(finance_router, prefix="/api/v1", tags=["Finance"])

# HCM router would be added here when fully implemented
# app.include_router(hcm_router, prefix="/api/v1", tags=["HCM"])
# app.include_router(scm_router, prefix="/api/v1", tags=["SCM"])
# app.include_router(mfg_router, prefix="/api/v1", tags=["Manufacturing"])
# app.include_router(crm_router, prefix="/api/v1", tags=["CRM"])


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "apps.erp.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
