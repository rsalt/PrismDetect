"""
Detection endpoints
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
import numpy as np
import cv2
from typing import List, Optional
import time

from api.dependencies import get_detector
from core.detector import ProductDetector

router = APIRouter(prefix="/detect", tags=["detection"])

@router.post("")
async def detect_product(
    file: UploadFile = File(...),
    min_confidence: Optional[float] = None,
    detector: ProductDetector = Depends(get_detector)
):
    """
    Detect products in uploaded image
    
    - **file**: Image file (JPEG, PNG, etc.)
    - **min_confidence**: Override default confidence threshold
    """
    start_time = time.time()
    
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="Image size exceeds 10MB")
        
        # Use PIL for safe loading and resizing (prevents OOM on large dimensions)
        try:
            from PIL import Image
            import io
            
            img = Image.open(io.BytesIO(contents))
            
            # Convert to RGB if needed (handles RGBA, Greyscale etc)
            if img.mode != 'RGB':
                img = img.convert('RGB')
                
            # Resize if too large (max 1280px)
            max_dim = 1280
            if max(img.size) > max_dim:
                img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            
            # Convert to numpy/OpenCV format (RGB -> BGR)
            image_rgb = np.array(img)
            image = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
            
        except Exception as e:
            # Fallback to cv2 if PIL fails (unlikely given requirements)
            # or if image format is specific to cv2
            nparr = np.frombuffer(contents, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Run detection
        results = detector.detect(image, min_confidence)
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000
        
        return {
            "success": True,
            "detections": [r.to_dict() for r in results],
            "count": len(results),
            "processing_time_ms": round(processing_time, 2)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch")
async def detect_batch(
    files: List[UploadFile] = File(...),
    detector: ProductDetector = Depends(get_detector)
):
    """
    Batch detection for multiple images
    """
    results = []
    
    for file in files:
        try:
            contents = await file.read()
            nparr = np.frombuffer(contents, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            detections = detector.detect(image)
            
            results.append({
                "filename": file.filename,
                "success": True,
                "detections": [r.to_dict() for r in detections]
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e)
            })
    
    return {
        "success": True,
        "total": len(files),
        "results": results
    }
