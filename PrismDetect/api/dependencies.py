"""
FastAPI dependencies
"""

from fastapi import Request
from core.detector import ProductDetector

def get_detector(request: Request) -> ProductDetector:
    """Get detector instance from app state"""
    return request.app.state.detector
