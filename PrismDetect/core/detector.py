"""
Main product detector with patch scanning and multi-stage validation
"""

import cv2
import numpy as np
import json
import pickle
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from loguru import logger

from core.clip_onnx import ONNXCLIP
from core.patch_scanner import PatchScanner
from core.index import ProductIndex
from core.validators.shape_validator import ShapeValidator
from core.validators.text_validator import TextValidator
from core.learning.auto_learner import AutoLearner

@dataclass
class DetectionResult:
    """Detection result data class"""
    product_id: str
    product_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    text_verified: bool
    shape_valid: bool
    processing_ms: float
    matched_keywords: List[str] = None
    
    def to_dict(self):
        result = {
            'product_id': self.product_id,
            'product_name': self.product_name,
            'confidence': round(self.confidence, 4),
            'bbox': {
                'x': self.bbox[0],
                'y': self.bbox[1],
                'width': self.bbox[2],
                'height': self.bbox[3]
            },
            'text_verified': self.text_verified,
            'shape_valid': self.shape_valid,
            'processing_ms': round(self.processing_ms, 2)
        }
        if self.matched_keywords:
            result['matched_keywords'] = self.matched_keywords
        return result

class ProductDetector:
    """Main product detector with multi-stage validation"""
    
    def __init__(self, config_path: str = "config/products.json", 
                 model_path: str = "models/clip_int8.onnx",
                 index_path: str = "data/index/product_index.faiss"):
        
        # Load configuration
        self.config_path = config_path
        self.config = self._load_config(config_path)
        
        # Initialize components
        logger.info("Initializing CLIP model...")
        self.clip = ONNXCLIP(model_path)
        
        logger.info("Initializing patch scanner...")
        self.scanner = PatchScanner(
            patch_size=self.config['system']['patch_scanner']['patch_size'],
            stride=self.config['system']['patch_scanner']['stride']
        )
        # Initialize index
        index_cfg = self.config['system']['index']
        logger.info(f"Initializing ProductIndex with dimension={index_cfg['dimension']}, type={index_cfg['type']}")
        self.index = ProductIndex(
            dimension=index_cfg['dimension'],
            index_path="data/index/product_index.faiss"
        )
        
        logger.info("Initializing validators...")
        self.shape_validator = ShapeValidator()
        self.text_validator = TextValidator()
        
        logger.info("Initializing auto-learner...")
        self.auto_learner = AutoLearner(
            enabled=self.config['system']['auto_learning']['enabled'],
            threshold=self.config['system']['auto_learning']['threshold'],
            max_refs=self.config['system']['auto_learning']['max_references_per_product']
        )
        
        # Load products
        self._load_products()
        
        logger.success(f"✅ Detector ready with {self.index.size} references")
    
    def _load_config(self, path: str) -> dict:
        """Load configuration from JSON"""
        with open(path, 'r') as f:
            return json.load(f)
    
    def _load_products(self):
        """Load all products and their references"""
        for product in self.config['products']:
            if not product.get('active', True):
                continue
                
            product_id = product['id']
            logger.info(f"Loading product: {product_id}")
            
            for ref in product.get('reference_images', []):
                img_path = ref['url']
                if not Path(img_path).exists():
                    logger.warning(f"Reference image not found: {img_path}")
                    continue
                
                try:
                    # Load and encode reference
                    img = cv2.imread(img_path)
                    if img is None:
                        continue
                    
                    # Get embedding
                    embedding = self.clip.encode(img)
                    
                    # Get shape ratio
                    shape_ratio = self.shape_validator.get_aspect_ratio(img)
                    
                    # Add to index
                    self.index.add_product(
                        product_id=product_id,
                        embedding=embedding,
                        shape_ratio=shape_ratio,
                        metadata={
                            'name': product['name'],
                            'keywords': product.get('keywords', []),
                            'validation': product.get('validation', {}),
                            'ref_id': ref['id']
                        }
                    )
                    
                    logger.debug(f"  Added reference: {ref['id']}")
                    
                except Exception as e:
                    logger.error(f"Error loading reference {ref['id']}: {e}")
        
        # Save index after loading
        self.index.save()
        
    def detect(self, image: np.ndarray, min_confidence: float = None) -> List[DetectionResult]:
        """
        Detect products in image with multi-stage validation
        """
        start_time = time.time()
        
        # NOTE: Resizing is handled in API route layer (api/routes/detect.py) using PIL
            
        # Use config threshold if not overridden
        if min_confidence is None:
            min_confidence = self.config['system'].get('min_confidence', 0.75)
        
        # Stage 1: Patch scanning
        logger.info(f"Starting patch scan for image {image.shape}")
        try:
            patches = self.scanner.scan(image)
            logger.info(f"Generated {len(patches)} patches")
        except Exception as e:
            logger.error(f"Patch scanning failed: {e}")
            return []
            
        # Store high-confidence candidates before running expensive OCR
        pre_nms_candidates = []
        
        for i, (patch, bbox) in enumerate(patches):
            if i % 10 == 0:
                logger.debug(f"Processing patch {i}/{len(patches)}")

            # Stage 2: Encode patch
            try:
                embedding = self.clip.encode(patch)
            except Exception as e:
                logger.error(f"CLIP encoding failed for patch {i}: {e}")
                continue
            
            # Stage 3: Search index
            matches = self.index.search(embedding, k=3)
            
            for candidate in matches:
                raw_sim = candidate['similarity']
                if raw_sim < min_confidence:
                    continue
                
                # Apply base scaling curve immediately to determine real confidence
                scaled_sim = min(1.0, raw_sim * 1.18)
                
                # Stage 4: Shape validation (Fast)
                actual_ratio = self.shape_validator.get_aspect_ratio(patch)
                expected_ratio = candidate['metadata'].get('shape_ratio', actual_ratio)
                tolerance = candidate['metadata'].get('validation', {}).get('shape_tolerance', 0.15)
                
                shape_valid = self.shape_validator.validate(
                    actual_ratio, 
                    expected_ratio, 
                    tolerance
                )
                
                if shape_valid:
                    scaled_sim = min(1.0, scaled_sim + 0.02)
                    
                pre_nms_candidates.append({
                    'product_id': candidate['product_id'],
                    'product_name': candidate['metadata']['name'],
                    'confidence': scaled_sim,
                    'bbox': bbox,
                    'shape_valid': shape_valid,
                    'keywords': candidate['metadata'].get('keywords', []),
                    'patch': patch
                })
        
        # Group candidates by product_id to ensure we only return 1 bounding box maximum per product type
        from collections import defaultdict
        product_groups = defaultdict(list)
        for cand in pre_nms_candidates:
            product_groups[cand['product_id']].append(cand)
            
        final_detections = []
        
        for product_id, cands in product_groups.items():
            # 1. Merge overlapping patches for this specific product to form full-object bounding boxes
            clusters = []
            
            for cand in cands:
                cand_bbox = cand['bbox'] # [x, y, w, h]
                matched_cluster = None
                
                # Check if this patch overlaps with any existing cluster for this product
                for cluster in clusters:
                    cb = cluster['bbox']
                    # Calculate Intersection over Union (IoU) or Intersection over Minimum (IoM)
                    x1 = max(cand_bbox[0], cb[0])
                    y1 = max(cand_bbox[1], cb[1])
                    x2 = min(cand_bbox[0] + cand_bbox[2], cb[0] + cb[2])
                    y2 = min(cand_bbox[1] + cand_bbox[3], cb[1] + cb[3])
                    
                    if x2 > x1 and y2 > y1:
                        # They overlap physically
                        matched_cluster = cluster
                        break
                        
                if matched_cluster:
                    # Expand cluster bounds
                    cb = matched_cluster['bbox']
                    new_x = min(cb[0], cand_bbox[0])
                    new_y = min(cb[1], cand_bbox[1])
                    new_max_x = max(cb[0] + cb[2], cand_bbox[0] + cand_bbox[2])
                    new_max_y = max(cb[1] + cb[3], cand_bbox[1] + cand_bbox[3])
                    matched_cluster['bbox'] = [new_x, new_y, new_max_x - new_x, new_max_y - new_y]
                    # Update confidence if this patch is stronger
                    matched_cluster['confidence'] = max(matched_cluster['confidence'], cand['confidence'])
                else:
                    # Create new cluster
                    clusters.append({
                        'product_id': cand['product_id'],
                        'product_name': cand['product_name'],
                        'confidence': cand['confidence'],
                        'bbox': list(cand_bbox),
                        'shape_valid': cand['shape_valid'],
                        'keywords': cand['keywords']
                    })
                    
            # 2. Sort the independent physical clusters for this product by confidence
            clusters.sort(key=lambda x: x['confidence'], reverse=True)
            
            # 3. Only keep the SINGLE BEST instance of this product "don't need to detect again"
            if clusters:
                best_cluster = clusters[0]
                
                # Stage 5: Expensive Text Validation ONLY on the final best cluster
                text_verified = False
                matched_keywords = []
                final_confidence = best_cluster['confidence']
                
                x, y, w, h = best_cluster['bbox']
                
                # Safety check: constrain bounding box to image dimensions
                x = max(0, x)
                y = max(0, y)
                w = min(w, image.shape[1] - x)
                h = min(h, image.shape[0] - y)
                best_cluster['bbox'] = (x, y, w, h)
                
                merged_patch = image[y:y+h, x:x+w]
                
                # Only run OCR if patch is valid size to prevent OpenCV segfault
                if merged_patch.size > 0 and best_cluster['keywords'] and (best_cluster['shape_valid'] or final_confidence > 0.9):
                    try:
                        # Resize massive merged patches down to reasonable sizes before OCR to prevent OOM
                        max_ocr_dim = 600
                        if max(w, h) > max_ocr_dim:
                            scale = max_ocr_dim / max(w, h)
                            ocr_patch = cv2.resize(merged_patch, (int(w*scale), int(h*scale)))
                        else:
                            ocr_patch = merged_patch
                            
                        text_verified, matched_keywords = self.text_validator.validate(
                            ocr_patch, 
                            best_cluster['keywords']
                        )
                        if text_verified:
                            final_confidence = min(1.0, final_confidence + 0.05)
                    except Exception as e:
                        logger.warning(f"Text validation failed for specific detection: {e}")
                        
                detection = DetectionResult(
                    product_id=best_cluster['product_id'],
                    product_name=best_cluster['product_name'],
                    confidence=final_confidence,
                    bbox=best_cluster['bbox'],
                    text_verified=text_verified,
                    shape_valid=best_cluster['shape_valid'],
                    matched_keywords=matched_keywords,
                    processing_ms=(time.time() - start_time) * 1000
                )
                final_detections.append(detection)
        
        # Auto-learn from high confidence detections
        for det in final_detections:
            if self.auto_learner.should_learn(det):
                x, y, w, h = det.bbox
                patch = image[y:y+h, x:x+w]
                self.auto_learner.learn(
                    image=patch,
                    detection=det,
                    detector=self
                )
            
        logger.info(f"Found {len(final_detections)} detections in {time.time()-start_time:.2f}s")
        
        return final_detections
    
    def add_product(self, product_config: dict) -> bool:
        """Add a new product to the system"""
        try:
            # Add to config
            self.config['products'].append(product_config)
            
            # Save config
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            # Load product references
            product_id = product_config['id']
            for ref in product_config.get('reference_images', []):
                img_path = ref['url']
                if Path(img_path).exists():
                    img = cv2.imread(img_path)
                    embedding = self.clip.encode(img)
                    shape_ratio = self.shape_validator.get_aspect_ratio(img)
                    
                    self.index.add_product(
                        product_id=product_id,
                        embedding=embedding,
                        shape_ratio=shape_ratio,
                        metadata={
                            'name': product_config['name'],
                            'keywords': product_config.get('keywords', []),
                            'validation': product_config.get('validation', {})
                        }
                    )
            
            self.index.save()
            logger.success(f"Added product: {product_config['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add product: {e}")
            return False
