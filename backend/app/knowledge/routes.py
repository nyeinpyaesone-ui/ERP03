from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.database import get_db
from app.audit.service import AuditService, AuditLogEntry
from app.skills.registry import SkillRegistry, SkillExecutionRequest
from app.config.service import ConfigService, ConfigValue
from app.knowledge.service import KnowledgeService, KnowledgeQuery

router = APIRouter(prefix="/api/v1/knowledge", tags=["Knowledge System"])

# ========== AUDIT ENDPOINTS ==========

class AuditQueryParams(BaseModel):
    table_name: Optional[str] = None
    record_id: Optional[str] = None
    actor_id: Optional[str] = None
    action: Optional[str] = None
    days: int = 30
    limit: int = 100
    offset: int = 0

@router.get("/audit/logs")
async def query_audit_logs(
    table_name: Optional[str] = None,
    record_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    service = AuditService(db)
    logs = await service.query_logs(
        table_name=table_name, record_id=record_id, actor_id=actor_id,
        action=action, limit=limit, offset=offset
    )
    return {"logs": logs, "count": len(logs)}

@router.get("/audit/integrity")
async def verify_audit_integrity(start_id: int = 1, db: AsyncSession = Depends(get_db)):
    service = AuditService(db)
    return await service.verify_integrity(start_id=start_id)

@router.get("/audit/statistics")
async def get_audit_statistics(days: int = 30, db: AsyncSession = Depends(get_db)):
    service = AuditService(db)
    return await service.get_statistics(days=days)

# ========== SKILL ENDPOINTS ==========

@router.get("/skills")
async def list_skills(
    category: Optional[str] = None,
    requires_approval: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    registry = SkillRegistry(db)
    skills = await registry.list_skills(category=category, requires_approval=requires_approval)
    return {"skills": skills}

@router.post("/skills/execute")
async def execute_skill(request: SkillExecutionRequest, db: AsyncSession = Depends(get_db)):
    registry = SkillRegistry(db)
    audit = AuditService(db)
    result = await registry.execute_skill(request, audit_service=audit)
    return result

@router.post("/skills/validate")
async def validate_skill_input(
    skill_code: str,
    input_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    registry = SkillRegistry(db)
    return await registry.validate_input(skill_code, input_data)

# ========== CONFIG ENDPOINTS ==========

@router.get("/config/{key}")
async def get_config(key: str, tenant_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    service = ConfigService(db)
    value = await service.get(key, tenant_id=tenant_id)
    if value is None:
        raise HTTPException(status_code=404, detail=f"Config key {key} not found")
    return {"key": key, "value": value}

@router.put("/config/{key}")
async def set_config(
    key: str,
    value: ConfigValue,
    tenant_id: Optional[str] = None,
    updated_by: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    service = ConfigService(db)
    return await service.set(
        key=key, value=value.config_value, config_type=value.config_type,
        category=value.category, description=value.description,
        tenant_id=tenant_id, updated_by=updated_by
    )

@router.get("/config/category/{category}")
async def get_config_by_category(category: str, tenant_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    service = ConfigService(db)
    return {"configs": await service.list_by_category(category, tenant_id)}

@router.get("/config/features/flags")
async def get_feature_flags(tenant_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    service = ConfigService(db)
    return {"flags": await service.get_feature_flags(tenant_id)}

# ========== KNOWLEDGE BASE ENDPOINTS ==========

@router.get("/articles/search")
async def search_knowledge(
    q: str,
    category_id: Optional[int] = None,
    difficulty: Optional[str] = None,
    limit: int = 5,
    db: AsyncSession = Depends(get_db)
):
    service = KnowledgeService(db)
    query = KnowledgeQuery(query=q, category_id=category_id, difficulty=difficulty, limit=limit)
    return {"results": await service.search(query)}

@router.get("/articles/{slug}")
async def get_article(slug: str, db: AsyncSession = Depends(get_db)):
    service = KnowledgeService(db)
    article = await service.get_article(slug)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@router.get("/articles/category/{category_id}")
async def get_articles_by_category(category_id: int, db: AsyncSession = Depends(get_db)):
    service = KnowledgeService(db)
    return {"articles": await service.get_by_category(category_id)}

@router.get("/learning-path")
async def get_learning_path(from_difficulty: str = "beginner", db: AsyncSession = Depends(get_db)):
    service = KnowledgeService(db)
    return {"path": await service.get_learning_path(from_difficulty)}

# ========== DOMAIN DATA ENDPOINTS ==========

@router.get("/domain/townships")
async def get_townships(zone: Optional[str] = None, region: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    conditions = ["is_active = TRUE"]
    params = {}
    if zone:
        conditions.append("delivery_zone = :zone")
        params["zone"] = zone
    if region:
        conditions.append("region_state = :region")
        params["region"] = region
    where_clause = " AND ".join(conditions)
    sql = f"SELECT * FROM townships WHERE {where_clause} ORDER BY name_en"
    result = await db.execute(sql, params)
    return {"townships": [dict(row) for row in result.fetchall()]}

@router.get("/domain/tax-rates")
async def get_tax_rates(tax_type: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    conditions = ["is_active = TRUE"]
    params = {}
    if tax_type:
        conditions.append("tax_type = :tax_type")
        params["tax_type"] = tax_type
    where_clause = " AND ".join(conditions)
    sql = f"SELECT * FROM tax_rates WHERE {where_clause} ORDER BY tax_type"
    result = await db.execute(sql, params)
    return {"tax_rates": [dict(row) for row in result.fetchall()]}

@router.get("/domain/border-stations")
async def get_border_stations(country: Optional[str] = None, status: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    conditions = []
    params = {}
    if country:
        conditions.append("country = :country")
        params["country"] = country
    if status:
        conditions.append("status = :status")
        params["status"] = status
    where_clause = " AND ".join(conditions) if conditions else "TRUE"
    sql = f"SELECT * FROM border_trade_stations WHERE {where_clause} ORDER BY country, station_name"
    result = await db.execute(sql, params)
    return {"stations": [dict(row) for row in result.fetchall()]}

@router.get("/domain/business-terms")
async def get_business_terms(domain: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    conditions = []
    params = {}
    if domain:
        conditions.append("domain = :domain")
        params["domain"] = domain
    where_clause = " AND ".join(conditions) if conditions else "TRUE"
    sql = f"SELECT * FROM business_terms WHERE {where_clause} ORDER BY term_en"
    result = await db.execute(sql, params)
    return {"terms": [dict(row) for row in result.fetchall()]}

@router.post("/domain/delivery-estimate")
async def get_delivery_estimate(origin: str, destination: str, weight_kg: float = 1000, db: AsyncSession = Depends(get_db)):
    sql = """
        SELECT tc.route_name, tc.distance_km, t.estimated_days,
               ROUND(tc.rate_per_ton_mmk * (:weight_kg / 1000), 2) AS cost_mmk,
               tc.terrain
        FROM trucking_corridors tc
        JOIN townships t ON t.name_en = :destination
        WHERE tc.route_name ILIKE '%' || :origin || '%'
        ORDER BY tc.distance_km LIMIT 1
    """
    result = await db.execute(sql, {"origin": origin, "destination": destination, "weight_kg": weight_kg})
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Route not found")
    return dict(row)

@router.post("/domain/calculate-tax")
async def calculate_tax(amount: float, tax_types: List[str], db: AsyncSession = Depends(get_db)):
    sql = """
        SELECT tax_type, tax_name_en, rate,
               ROUND(:amount * rate, 2) AS tax_amount,
               ROUND(:amount * (1 + rate), 2) AS total_with_tax
        FROM tax_rates
        WHERE tax_type = ANY(:tax_types) AND is_active = TRUE
        ORDER BY tax_type
    """
    result = await db.execute(sql, {"amount": amount, "tax_types": tax_types})
    return {"breakdown": [dict(row) for row in result.fetchall()]}

