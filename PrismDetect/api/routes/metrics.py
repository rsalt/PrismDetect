"""
Prometheus metrics endpoints
"""

from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import Counter, Histogram, Gauge
import time

router = APIRouter(tags=["metrics"])

# Define metrics
detection_counter = Counter(
    'prismdetect_detections_total',
    'Total number of detections',
    ['product_id']
)

detection_latency = Histogram(
    'prismdetect_detection_latency_seconds',
    'Detection latency in seconds',
    buckets=[0.1, 0.2, 0.3, 0.5, 0.75, 1.0, 2.0]
)

active_products = Gauge(
    'prismdetect_active_products',
    'Number of active products'
)

reference_count = Gauge(
    'prismdetect_references_total',
    'Total number of reference images'
)

@router.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

# Export metrics functions for use in other modules
def record_detection(product_id: str, duration: float):
    """Record detection metrics"""
    detection_counter.labels(product_id=product_id).inc()
    detection_latency.observe(duration)
