"""
Health check endpoints
"""

from fastapi import APIRouter, Depends
import time
import platform
import psutil

from api.dependencies import get_detector
from core.detector import ProductDetector

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check(detector: ProductDetector = Depends(get_detector)):
    """Health check endpoint"""
    
    # System info
    system_info = {
        "platform": platform.system(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(),
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_available": round(psutil.virtual_memory().available / (1024**3), 2),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_free": round(psutil.disk_usage('/').free / (1024**3), 2)
    }
    
    # Service info
    service_info = {
        "status": "healthy",
        "products_loaded": len([p for p in detector.config['products'] if p.get('active', True)]),
        "references_loaded": detector.index.size,
        "auto_learning": detector.auto_learner.enabled,
        "model": detector.clip.input_name,
        "timestamp": time.time()
    }
    
    return {
        "service": service_info,
        "system": system_info
    }

@router.get("/readiness")
async def readiness_check(detector: ProductDetector = Depends(get_detector)):
    """Readiness probe for orchestration"""
    if detector and detector.index.size > 0:
        return {"status": "ready"}
    return {"status": "not ready"}

@router.get("/liveness")
async def liveness_check():
    """Liveness probe for orchestration"""
    return {"status": "alive"}
