from prometheus_client import Counter, Histogram, make_asgi_app

REQUEST_COUNT = Counter(
    "erp03_http_requests_total",
    "Total HTTP requests handled by ERP03",
    ("method", "route", "status"),
)
REQUEST_LATENCY = Histogram(
    "erp03_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ("method", "route"),
)
metrics_app = make_asgi_app()
