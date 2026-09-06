"""
Finance Module API Router
Aggregates all finance sub-module routers
"""
from fastapi import APIRouter

from apps.erp.modules.finance.general_ledger_api import router as gl_router
from apps.erp.modules.finance.accounts_payable_api import router as ap_router
from apps.erp.modules.finance.accounts_receivable_api import router as ar_router
from apps.erp.modules.finance.cash_management_api import router as cash_router
from apps.erp.modules.finance.fixed_assets_api import router as fa_router
from apps.erp.modules.finance.budgeting_api import router as budget_router

router = APIRouter(prefix="/finance", tags=["Finance"])

# Include all finance sub-routers
router.include_router(gl_router)
router.include_router(ap_router)
router.include_router(ar_router)
router.include_router(cash_router)
router.include_router(fa_router)
router.include_router(budget_router)
