"""
Pydantic settings management
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    API_HOST: str = Field("0.0.0.0", env="API_HOST")
    API_PORT: int = Field(8000, env="API_PORT")
    API_WORKERS: int = Field(2, env="API_WORKERS")
    DEBUG: bool = Field(False, env="DEBUG")
    ENVIRONMENT: str = Field("production", env="ENVIRONMENT")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(["*"], env="CORS_ORIGINS")
    
    # Paths
    CONFIG_PATH: str = Field("config/products.json", env="CONFIG_PATH")
    MODEL_PATH: str = Field("models/clip_int8.onnx", env="MODEL_PATH")
    INDEX_PATH: str = Field("data/index/product_index.faiss", env="INDEX_PATH")
    
    # Detection Settings
    MIN_CONFIDENCE: float = Field(0.75, env="MIN_CONFIDENCE")
    PATCH_SIZE: int = Field(224, env="PATCH_SIZE")
    PATCH_STRIDE: int = Field(112, env="PATCH_STRIDE")
    
    # Auto Learning
    AUTO_LEARN_ENABLED: bool = Field(True, env="AUTO_LEARN_ENABLED")
    AUTO_LEARN_THRESHOLD: float = Field(0.95, env="AUTO_LEARN_THRESHOLD")
    MAX_REFERENCES_PER_PRODUCT: int = Field(50, env="MAX_REFERENCES_PER_PRODUCT")
    
    # Limits
    MAX_IMAGE_SIZE_MB: int = Field(10, env="MAX_IMAGE_SIZE_MB")
    REQUEST_TIMEOUT_SECONDS: int = Field(30, env="REQUEST_TIMEOUT_SECONDS")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings"""
    return Settings()

settings = get_settings()
