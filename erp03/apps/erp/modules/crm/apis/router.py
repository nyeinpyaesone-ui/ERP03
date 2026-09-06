"""
CRM Module API Router
Aggregates all Customer Relationship Management sub-module routers
"""
from fastapi import APIRouter

router = APIRouter(prefix="/crm", tags=["CRM"])

@router.get("/status")
async def crm_status():
    """CRM module status endpoint"""
    return {"module": "CRM", "status": "initialized", "version": "1.0.0"}
