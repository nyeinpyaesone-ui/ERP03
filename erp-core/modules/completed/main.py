from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import SlowRateLimiter
from slowapi.util import get_remote_address
from app.routers import auth, users, inventory, health
from app.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="ERP03 Production System"
)

# CORS Configuration - Secure with specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiter Setup
limiter = SlowRateLimiter(key_func=get_remote_address)
app.state.limiter = limiter

# Include Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["Inventory"])
app.include_router(health.router, prefix="/api/v1", tags=["Health"])

@app.get("/")
async def root():
    return {"message": "ERP03 API - Production Ready", "version": "1.0.0"}
