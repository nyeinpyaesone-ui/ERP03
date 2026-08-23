"""
ERP03 v1.0.0 - Core Module Initialization
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.database.session import get_db_session
from app.core.security.auth import JWTProvider
from app.modules.finance.apis.router import router as finance_router
from app.modules.hcm.apis.router import router as hcm_router
from app.modules.scm.apis.router import router as scm_router
from app.modules.manufacturing.apis.router import router as mfg_router
from app.modules.crm.apis.router import router as crm_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB connections, load plugins
    print("ERP03 Core Starting...")
    yield
    # Shutdown: Close connections
    print("ERP03 Core Shutting down...")

app = FastAPI(
    title="ERP03 Core",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Domain Routers
app.include_router(finance_router, prefix="/api/v1/finance", tags=["Finance"])
app.include_router(hcm_router, prefix="/api/v1/hcm", tags=["HCM"])
app.include_router(scm_router, prefix="/api/v1/scm", tags=["SCM"])
app.include_router(mfg_router, prefix="/api/v1/manufacturing", tags=["Manufacturing"])
app.include_router(crm_router, prefix="/api/v1/crm", tags=["CRM"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
