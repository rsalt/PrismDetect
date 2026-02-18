import os
# Fix for macOS segfaults with transformers/tokenizers
os.environ["TOKENIZERS_PARALLELISM"] = "false"
# Fix for OpenMP conflicts
os.environ["OMP_NUM_THREADS"] = "1"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time
from loguru import logger

from api.routes import detect, products, health, metrics
from core.detector import ProductDetector
from config.settings import settings

# Global detector instance
detector = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for startup/shutdown events"""
    global detector
    
    # Startup
    logger.info("🚀 Starting PrismDetect API")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Initialize detector
    detector = ProductDetector(
        config_path=settings.CONFIG_PATH,
        model_path=settings.MODEL_PATH,
        index_path=settings.INDEX_PATH
    )
    app.state.detector = detector
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down PrismDetect API")
    
    # Save index on shutdown
    if detector:
        detector.index.save()

# Create FastAPI app
app = FastAPI(
    title="PrismDetect API",
    description="Lightweight AI-based product detection system",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(detect.router, tags=["Detection"])
app.include_router(products.router, tags=["Products"])
app.include_router(metrics.router, tags=["Metrics"])

# Mount static files
app.mount("/data", StaticFiles(directory="data"), name="data")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "PrismDetect API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "detect": "/detect",
            "products": "/products",
            "health": "/health",
            "metrics": "/metrics",
            "docs": "/docs" if settings.DEBUG else None
        }
    }
