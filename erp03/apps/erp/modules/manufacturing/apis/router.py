"""
Manufacturing Module API Router
Aggregates all Manufacturing sub-module routers
"""
from fastapi import APIRouter

router = APIRouter(prefix="/manufacturing", tags=["Manufacturing"])

@router.get("/status")
async def mfg_status():
    """Manufacturing module status endpoint"""
    return {"module": "Manufacturing", "status": "initialized", "version": "1.0.0"}
