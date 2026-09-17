from fastapi import FastAPI
from app.api.health import router as health_router

app = FastAPI(title="ERP03 API", version="1.0.0")
app.include_router(health_router)

@app.get("/api/v1")
def api_root():
    return {"service": "erp03", "status": "ready"}
