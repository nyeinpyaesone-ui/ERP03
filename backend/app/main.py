from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from time import perf_counter

from app.database import engine, Base
from app.routers import (
    auth, crm, hr, inventory, finance, projects,
    ai, documents, reports, workflows, payments,
    integrations, analytics, admin, websocket,
    bulk_import_export, migrations
)
from app.config import settings

HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise Resource Planning with AI-powered features",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

@app.middleware("http")
async def metrics_middleware(request, call_next):
    start = perf_counter()
    response = await call_next(request)
    path = request.url.path
    HTTP_REQUESTS.labels(request.method, path, str(response.status_code)).inc()
    HTTP_REQUEST_DURATION.labels(request.method, path).observe(perf_counter() - start)
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(crm.router, prefix="/api/v1/crm", tags=["CRM"])
app.include_router(hr.router, prefix="/api/v1/hr", tags=["HR"])
app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["Inventory"])
app.include_router(finance.router, prefix="/api/v1/finance", tags=["Finance"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["Workflows"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["Payments"])
app.include_router(integrations.router, prefix="/api/v1/integrations", tags=["Integrations"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(websocket.router, prefix="/api/v1/ws", tags=["WebSocket"])
app.include_router(bulk_import_export.router, prefix="/api/v1/bulk", tags=["Bulk Import/Export"])
app.include_router(migrations.router, prefix="/api/v1/migrations", tags=["Migrations"])

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "features": [
            "Core ERP (CRM, HR, Inventory, Finance, Projects)",
            "AI Chat & RAG",
            "Document Management",
            "Reports & Analytics",
            "Workflow Automation",
            "Stripe Payments",
            "WebSocket Real-time",
            "PWA with Offline Support",
            "AI Forecasting",
            "Bulk Import/Export",
            "Alembic Migrations"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/metrics", include_in_schema=False)
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
