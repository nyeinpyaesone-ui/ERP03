from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import init_db

# Import domain routers
from app.domain.identity.api.identity_router import router as identity_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    print("ERP-CORE database initialized")
    
    # Load plugins (cold start)
    from app.plugins.loader import PluginLoader
    loader = PluginLoader()
    await loader.load_all_plugins()
    
    yield
    
    # Shutdown
    print("ERP-CORE shutting down")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Enterprise Resource Planning Core System",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register core domain routers
app.include_router(identity_router)

@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
