"""
Product management endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List, Optional
import json
import cv2
import numpy as np
from pathlib import Path
import time
import shutil
from loguru import logger

from api.dependencies import get_detector
from core.detector import ProductDetector

router = APIRouter(prefix="/products", tags=["products"])

@router.get("")
async def list_products(detector: ProductDetector = Depends(get_detector)):
    """List all configured products"""
    products = []
    
    for product in detector.config.get('products', []):
        # Count references
        ref_count = 0
        for uid, meta in detector.index.metadata.items():
            if meta['product_id'] == product['id']:
                ref_count += 1
        
        products.append({
            "id": product['id'],
            "name": product['name'],
            "active": product.get('active', True),
            "reference_count": ref_count,
            "keywords": product.get('keywords', []),
            "created_at": product.get('created_at')
        })
    
    return {"products": products}

@router.get("/{product_id}")
async def get_product(
    product_id: str,
    detector: ProductDetector = Depends(get_detector)
):
    """Get detailed product information"""
    # Find product in config
    product = None
    for p in detector.config['products']:
        if p['id'] == product_id:
            product = p
            break
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get references from index
    references = []
    for uid, meta in detector.index.metadata.items():
        if meta['product_id'] == product_id:
            references.append({
                "id": meta['metadata'].get('ref_id', uid),
                "shape_ratio": meta['shape_ratio'],
                "learned": meta['metadata'].get('learned', False),
                "added_at": meta.get('added_at')
            })
    
    return {
        **product,
        "references": references,
        "reference_count": len(references)
    }

@router.post("")
async def add_product(
    product_data: dict,
    detector: ProductDetector = Depends(get_detector)
):
    """Add a new product"""
    try:
        # Validate required fields
        required = ['id', 'name', 'reference_images']
        for field in required:
            if field not in product_data:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Missing required field: {field}"
                )
        
        # Add product
        success = detector.add_product(product_data)
        
        if success:
            return {
                "success": True,
                "message": f"Product {product_data['name']} added successfully",
                "product_id": product_data['id']
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to add product")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{product_id}")
async def update_product(
    product_id: str,
    product_data: dict,
    detector: ProductDetector = Depends(get_detector)
):
    """Update an existing product (e.g., name rename, toggle lock)"""
    try:
        product = None
        for p in detector.config['products']:
            if p['id'] == product_id:
                product = p
                break
                
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
            
        if "name" in product_data:
            product['name'] = product_data["name"]
            
        if "locked" in product_data:
            product['locked'] = product_data["locked"]
        
        # Save config
        with open(detector.config_path, 'w') as f:
            json.dump(detector.config, f, indent=2)
            
        # Update metadata in index
        updated_count = 0
        if "name" in product_data:
            for uid, meta in detector.index.metadata.items():
                if meta['product_id'] == product_id:
                    meta['metadata']['name'] = product['name']
                    updated_count += 1
                    
            if updated_count > 0:
                detector.index.save()
            
        return {"success": True, "message": f"Product updated. Adjusted {updated_count} index references."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating product: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    detector: ProductDetector = Depends(get_detector)
):
    """Delete an entire product and all its references"""
    try:
        # Find product
        product_idx = -1
        product = None
        for i, p in enumerate(detector.config.get('products', [])):
            if p['id'] == product_id:
                product_idx = i
                product = p
                break
                
        if product_idx == -1:
            raise HTTPException(status_code=404, detail="Product not found")
            
        if product.get('locked', False):
            raise HTTPException(status_code=400, detail="Product is locked and cannot be deleted")
            
        # Remove from config
        detector.config['products'].pop(product_idx)
        
        with open(detector.config_path, 'w') as f:
            json.dump(detector.config, f, indent=2)
            
        # Delete directory
        ref_dir = Path(f"data/references/{product_id}")
        if ref_dir.exists():
            try:
                shutil.rmtree(ref_dir)
                logger.info(f"Deleted product references directory: {ref_dir}")
            except Exception as e:
                logger.warning(f"Failed to delete references directory {ref_dir}: {e}")
                
        # Remove from FAISS index
        uids_to_remove = []
        for uid, meta in detector.index.metadata.items():
            if meta['product_id'] == product_id:
                uids_to_remove.append(uid)
                
        for uid in uids_to_remove:
            detector.index.remove_product(uid)
            
        if uids_to_remove:
            detector.index.save()
            logger.info(f"Removed {len(uids_to_remove)} vectors for product {product_id}")
            
        return {"success": True, "message": f"Product deleted including {len(uids_to_remove)} vectors."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting product: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{product_id}/references")
async def add_reference(
    product_id: str,
    file: UploadFile = File(...),
    angle: Optional[str] = "unknown",
    detector: ProductDetector = Depends(get_detector)
):
    """Add reference image to existing product"""
    try:
        # Check if product exists
        product = None
        for p in detector.config['products']:
            if p['id'] == product_id:
                product = p
                break
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        if product.get('locked', False):
            raise HTTPException(status_code=400, detail="Product is locked and cannot receive new references")
        
        # Save image
        contents = await file.read()
        ref_dir = Path(f"data/references/{product_id}")
        ref_dir.mkdir(parents=True, exist_ok=True)
        
        ref_id = f"ref_{int(time.time())}"
        img_path = ref_dir / f"{ref_id}.jpg"
        
        with open(img_path, 'wb') as f:
            f.write(contents)
        
        # Add to config
        product.setdefault('reference_images', []).append({
            "id": ref_id,
            "url": str(img_path),
            "angle": angle,
            "added_at": time.time()
        })
        
        # Save config
        with open(detector.config_path, 'w') as f:
            json.dump(detector.config, f, indent=2)
        
        # Load into index
        logger.info(f"Processing reference image: {img_path}")
        img = cv2.imread(str(img_path))
        if img is None:
             raise ValueError(f"Failed to read image: {img_path}")
        logger.info(f"Image read successfully shape={img.shape}")
        
        logger.info("Encoding with CLIP...")
        embedding = detector.clip.encode(img)
        logger.info("CLIP encoding successful")
        
        logger.info("Calculating shape ratio...")
        shape_ratio = detector.shape_validator.get_aspect_ratio(img)
        
        logger.info("Adding to index...")
        detector.index.add_product(
            product_id=product_id,
            embedding=embedding,
            shape_ratio=shape_ratio,
            metadata={
                'name': product['name'],
                'keywords': product.get('keywords', []),
                'validation': product.get('validation', {}),
                'ref_id': ref_id
            }
        )
        
        detector.index.save()
        logger.info("Index saved")
        
        return {
            "success": True,
            "product_id": product_id,
            "reference_id": ref_id,
            "path": str(img_path)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error adding reference: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error: {e!r}")
@router.delete("/{product_id}/references/{ref_id}")
async def delete_reference(
    product_id: str,
    ref_id: str,
    detector: ProductDetector = Depends(get_detector)
):
    """Delete a reference image"""
    try:
        # 1. Find product in config
        product = None
        for p in detector.config['products']:
            if p['id'] == product_id:
                product = p
                break
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
            
        if product.get('locked', False):
            raise HTTPException(status_code=400, detail="Product is locked and its references cannot be deleted")
        
        # 2. Find and remove reference from config
        ref_image = None
        if 'reference_images' in product:
            for i, ref in enumerate(product['reference_images']):
                if ref['id'] == ref_id:
                    ref_image = ref
                    product['reference_images'].pop(i)
                    break
        
        if not ref_image:
           # If not in config, it might still be in index or disk, but let's assume 404 for now
           # or proceed to try verify index/disk cleanup if we want to be robust. 
           # For now, consistent behavior:
           raise HTTPException(status_code=404, detail="Reference not found")

        # 3. Delete file from disk
        try:
            file_path = Path(ref_image['url'])
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to delete file {ref_image['url']}: {e}")

        # 4. Save config
        with open(detector.config_path, 'w') as f:
            json.dump(detector.config, f, indent=2)

        # 5. Remove from FAISS index
        # Find uid for this ref_id
        uid_to_remove = -1
        for uid, meta in detector.index.metadata.items():
            if meta['metadata'].get('ref_id') == ref_id:
                uid_to_remove = uid
                break
        
        if uid_to_remove != -1:
            detector.index.remove_product(uid_to_remove)
            detector.index.save()
            logger.info(f"Removed reference {ref_id} (uid={uid_to_remove}) from FAISS")
        else:
            logger.warning(f"Reference {ref_id} not found in FAISS index")

        return {"success": True, "message": "Reference deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting reference: {e}")
        raise HTTPException(status_code=500, detail=str(e))
