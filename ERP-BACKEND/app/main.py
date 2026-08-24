from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.config import settings
from app.middleware.error_handler import register_exception_handlers, error_handler_middleware
from app.plugins import setup_plugins, CORE_MODULES

# Import domain modules
from app.domains.auth import auth, user
from app.domains.users import users
from app.domains.permissions import permissions
from app.domains.crm import crm
from app.domains.hr import hr
from app.domains.finance import finance
from app.domains.inventory import inventory, inventory_service, regulated_inventory, regulated_inventory_service
from app.domains.projects import projects, project
from app.domains.documents import documents
from app.domains.workflows import workflows, workflow
from app.domains.payments import payments
from app.domains.analytics import analytics, analytics_service
from app.domains.search import search, search_service
from app.domains.integrations import integrations
from app.domains.websocket import websocket
from app.domains.admin import admin, system, activity_log
from app.domains.health import health

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="ERP03 Production System with Plugin Architecture"
)

# Register exception handlers
register_exception_handlers(app)

# Add error handler middleware
app.middleware("http")(error_handler_middleware)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS else ["*"]],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiter Setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Track core modules
app.state.core_modules = CORE_MODULES

# Setup plugin system
plugin_manager = setup_plugins(app, plugins_dir="/workspace/ERP-BACKEND/app/plugins")

# Include Core Routers (Built-in modules)
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(permissions.router, prefix="/api/v1/permissions", tags=["Permissions"])
app.include_router(crm.router, prefix="/api/v1/crm", tags=["CRM"])
app.include_router(hr.router, prefix="/api/v1/hr", tags=["HR"])
app.include_router(finance.router, prefix="/api/v1/finance", tags=["Finance"])
app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["Inventory"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["Workflows"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["Payments"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])
app.include_router(integrations.router, prefix="/api/v1/integrations", tags=["Integrations"])
app.include_router(websocket.router, prefix="/api/v1/ws", tags=["WebSocket"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(health.router, prefix="/api/v1", tags=["Health"])

# AI Assistant router
from app.ai.assistant import build_router as build_ai_router
app.include_router(build_ai_router(), prefix="/api/v1/ai", tags=["AI Assistant"])

@app.get("/")
async def root():
    return {
        "message": "ERP03 API - Production Ready with Plugin Support",
        "version": "1.0.0",
        "core_modules": len(CORE_MODULES),
        "plugins_enabled": True
    }

@app.get("/api/v1/plugins")
async def list_plugins():
    """List all loaded plugins."""
    return {"plugins": plugin_manager.list_plugins()}
