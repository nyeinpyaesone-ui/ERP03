from pydantic import BaseModel, Field


class RuntimeSettings(BaseModel):
    erp_base_url: str = Field(default="http://erp-backend:8000/integration/v1")
    service_token: str = Field(default="")
    request_timeout_seconds: float = Field(default=5.0, gt=0, le=30)
    max_retries: int = Field(default=2, ge=0, le=5)


def load_settings() -> RuntimeSettings:
    import os
    return RuntimeSettings(
        erp_base_url=os.getenv("ERP_INTEGRATION_BASE_URL", "http://erp-backend:8000/integration/v1").rstrip("/"),
        service_token=os.getenv("ERP_SERVICE_TOKEN", ""),
        request_timeout_seconds=float(os.getenv("ERP_REQUEST_TIMEOUT_SECONDS", "5")),
        max_retries=int(os.getenv("ERP_MAX_RETRIES", "2")),
    )
