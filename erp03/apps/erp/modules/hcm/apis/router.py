"""
HCM Module API Router
Aggregates all HCM sub-module routers
"""
from fastapi import APIRouter

router = APIRouter(prefix="/hcm", tags=["HCM"])

@router.get("/status")
async def hcm_status():
    """HCM module status endpoint"""
    return {"module": "HCM", "status": "initialized", "version": "1.0.0"}
