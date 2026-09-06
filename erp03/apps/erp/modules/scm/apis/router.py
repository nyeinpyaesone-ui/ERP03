"""
SCM Module API Router
Aggregates all Supply Chain Management sub-module routers
"""
from fastapi import APIRouter

router = APIRouter(prefix="/scm", tags=["SCM"])

@router.get("/status")
async def scm_status():
    """SCM module status endpoint"""
    return {"module": "SCM", "status": "initialized", "version": "1.0.0"}
