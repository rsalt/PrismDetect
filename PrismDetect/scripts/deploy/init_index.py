#!/usr/bin/env python3
"""
Initialize FAISS index from product configuration
Run once after setting up products
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.detector import ProductDetector
from loguru import logger

def init_index():
    """Initialize product index"""
    
    logger.info("🚀 Initializing product index...")
    
    # Initialize detector (this will load all products)
    detector = ProductDetector(
        config_path="config/products.json",
        model_path="models/clip_int8.onnx",
        index_path="data/index/product_index.faiss"
    )
    
    # Print stats
    stats = detector.index.get_stats()
    logger.success(f"✅ Index initialized with {stats['total_embeddings']} embeddings")
    logger.info(f"   Products: {stats['unique_products']}")
    logger.info(f"   Dimension: {stats['dimension']}")
    logger.info(f"   Type: {stats['index_type']}")
    
    # Save index
    detector.index.save()
    logger.success("✅ Index saved to disk")

if __name__ == "__main__":
    init_index()
