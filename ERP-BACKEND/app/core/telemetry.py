"""OpenTelemetry instrumentation for ERP03 backend."""

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def _get_engine():
    """Lazily import the engine to avoid import-time failures."""
    from app.db.session import engine

    return engine


REQUEST_COUNT = None
REQUEST_LATENCY = None


def init_telemetry(service_name: str = "erp03-backend") -> None:
    """Initialize OpenTelemetry tracing and metrics."""
    global REQUEST_COUNT, REQUEST_LATENCY

    resource = Resource(
        attributes={
            "service.name": service_name,
            "service.version": "1.0.0",
            "deployment.environment": "production",
        }
    )

    trace.set_tracer_provider(TracerProvider(resource=resource))
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint="http://otel-collector:4317"))
    )

    reader = PeriodicExportingMetricReader(
        exporter=OTLPMetricExporter(endpoint="http://otel-collector:4317"),
        export_interval_millis=15000,
    )
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))

    REQUEST_COUNT = metrics.get_meter(__name__).create_counter(
        "erp03_requests_total", unit="1", description="Total HTTP requests"
    )
    REQUEST_LATENCY = metrics.get_meter(__name__).create_histogram(
        "erp03_request_duration_ms", unit="ms", description="Request duration"
    )


def instrument_app(app) -> None:
    """Instrument FastAPI and SQLAlchemy."""
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=_get_engine())
