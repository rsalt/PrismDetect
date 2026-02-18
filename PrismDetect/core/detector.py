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
        
        Args:
            image: BGR image as numpy array
            min_confidence: Override default confidence threshold
            
        Returns:
            List of DetectionResult objects
        """
        start_time = time.time()
        
        # NOTE: Resizing is now handled in API route layer (api/routes/detect.py) using PIL
        # to prevent OOM before we even get here.
            
        all_detections = []
        
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
            candidates = self.index.search(embedding, k=3)
            
            for candidate in candidates:
                if candidate['similarity'] < min_confidence:
                    continue
                
                # Stage 4: Shape validation
                actual_ratio = self.shape_validator.get_aspect_ratio(patch)
                expected_ratio = candidate['metadata'].get('shape_ratio', actual_ratio)
                tolerance = candidate['metadata'].get('validation', {}).get('shape_tolerance', 0.15)
                
                shape_valid = self.shape_validator.validate(
                    actual_ratio, 
                    expected_ratio, 
                    tolerance
                )
                
                # Stage 5: Text validation
                text_verified = False
                matched_keywords = []
                
                if shape_valid or candidate['similarity'] > 0.9:
                    keywords = candidate['metadata'].get('keywords', [])
                    if keywords:
                        try:
                            # Verify text only if high confidence or shape valid
                            # Text validation is expensive and crash-prone
                            text_verified, matched_keywords = self.text_validator.validate(
                                patch, 
                                keywords
                            )
                        except Exception as e:
                            logger.warning(f"Text validation failed for patch {i}: {e}")
                
                # Stage 6: Final decision
                # Accept if it passed the min_confidence check (already done in Stage 3)
                if True:
                    
                    # Adjust confidence based on validations
                    final_confidence = candidate['similarity']
                    if text_verified:
                        final_confidence = min(1.0, final_confidence + 0.05)
                    if shape_valid:
                        final_confidence = min(1.0, final_confidence + 0.02)
                    
                    detection = DetectionResult(
                        product_id=candidate['product_id'],
                        product_name=candidate['metadata']['name'],
                        confidence=final_confidence,
                        bbox=bbox,
                        text_verified=text_verified,
                        shape_valid=shape_valid,
                        matched_keywords=matched_keywords,
                        processing_ms=(time.time() - start_time) * 1000
                    )
                    
                    all_detections.append(detection)
        
        # Remove duplicates (keep highest confidence per product)
        final_detections = {}
        for det in all_detections:
            key = f"{det.product_id}_{det.bbox}"
            if key not in final_detections or det.confidence > final_detections[key].confidence:
                final_detections[key] = det
        
        # Auto-learn from high confidence detections
        for det in final_detections.values():
            if self.auto_learner.should_learn(det):
                x, y, w, h = det.bbox
                patch = image[y:y+h, x:x+w]
                self.auto_learner.learn(
                    image=patch,
                    detection=det,
                    detector=self
                )
        
        # Apply Non-Maximum Suppression (NMS)
        result_list = list(final_detections.values())
        final_list = []
        if result_list:
            # Sort by confidence
            result_list.sort(key=lambda x: x.confidence, reverse=True)
            
            keep = []
            while result_list:
                current = result_list.pop(0)
                keep.append(current)
                
                # Compare with remaining
                remaining = []
                for other in result_list:
                    # Calculate IoU
                    x1 = max(current.bbox[0], other.bbox[0])
                    y1 = max(current.bbox[1], other.bbox[1])
                    x2 = min(current.bbox[0] + current.bbox[2], other.bbox[0] + other.bbox[2])
                    y2 = min(current.bbox[1] + current.bbox[3], other.bbox[1] + other.bbox[3])
                    
                    intersection = max(0, x2 - x1) * max(0, y2 - y1)
                    area1 = current.bbox[2] * current.bbox[3]
                    area2 = other.bbox[2] * other.bbox[3]
                    union = area1 + area2 - intersection
                    
                    iou = intersection / union if union > 0 else 0
                    
                    # If overlap is too high, suppress (unless different product)
                    if iou < 0.3 or current.product_id != other.product_id:
                        remaining.append(other)
                
                result_list = remaining
            
            final_list = keep
            
        logger.info(f"Found {len(final_list)} detections in {time.time()-start_time:.2f}s")
        
        return final_list
    
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
