"""
Auto-learning module - Improves system over time
"""

import time
import numpy as np
import cv2
from pathlib import Path
from typing import Optional
from loguru import logger

class AutoLearner:
    """Automatic learning from high-confidence detections"""
    
    def __init__(self, enabled: bool = True, threshold: float = 0.95, 
                 max_refs: int = 50):
        """
        Initialize auto-learner
        
        Args:
            enabled: Whether auto-learning is enabled
            threshold: Confidence threshold for learning
            max_refs: Maximum references per product
        """
        self.enabled = enabled
        self.threshold = threshold
        self.max_refs = max_refs
        self.learned_count = 0
        
        # Create directory for learned references
        self.learned_dir = Path("data/references/learned")
        self.learned_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Auto-learner initialized: enabled={enabled}, threshold={threshold}")
    
    def should_learn(self, detection) -> bool:
        """
        Check if detection should be learned
        
        Args:
            detection: DetectionResult object
            
        Returns:
            True if should learn
        """
        return (self.enabled and 
                detection.confidence >= self.threshold and 
                detection.text_verified)
    
    def learn(self, image: np.ndarray, detection, detector) -> bool:
        """
        Learn from a detection
        
        Args:
            image: Image patch of the detection
            detection: DetectionResult object
            detector: ProductDetector instance
            
        Returns:
            True if learning successful
        """
        try:
            product_id = detection.product_id
            
            # Generate reference ID
            timestamp = int(time.time())
            ref_id = f"auto_{timestamp}_{self.learned_count}"
            
            # Save image
            img_path = self.learned_dir / f"{product_id}_{ref_id}.jpg"
            cv2.imwrite(str(img_path), image)
            
            # Get embedding
            embedding = detector.clip.encode(image)
            
            # Get shape ratio
            shape_ratio = detector.shape_validator.get_aspect_ratio(image)
            
            # Add to index
            detector.index.add_product(
                product_id=product_id,
                embedding=embedding,
                shape_ratio=shape_ratio,
                metadata={
                    'name': detection.product_name,
                    'keywords': [],  # No keywords needed for learned refs
                    'validation': {},
                    'ref_id': ref_id,
                    'learned': True,
                    'source_confidence': detection.confidence,
                    'timestamp': timestamp
                }
            )
            
            # Save index
            detector.index.save()
            
            self.learned_count += 1
            logger.success(f"🤖 Learned new variation for {product_id} (confidence: {detection.confidence:.3f})")
            
            # Check if we need to prune
            self._prune_if_needed(product_id, detector)
            
            return True
            
        except Exception as e:
            logger.error(f"Auto-learning failed: {e}")
            return False
    
    def _prune_if_needed(self, product_id: str, detector):
        """
        Remove oldest references if exceeding limit
        
        Args:
            product_id: Product ID
            detector: ProductDetector instance
        """
        # Count references for this product
        product_refs = []
        for uid, meta in detector.index.metadata.items():
            if meta['product_id'] == product_id:
                product_refs.append((uid, meta))
        
        if len(product_refs) > self.max_refs:
            # Sort by timestamp (oldest first)
            product_refs.sort(key=lambda x: x[1].get('metadata', {}).get('timestamp', 0))
            
            # Remove oldest until under limit
            to_remove = len(product_refs) - self.max_refs
            for i in range(to_remove):
                uid, _ = product_refs[i]
                detector.index.remove_product(uid)
                logger.info(f"Pruned old reference {uid} for {product_id}")
    
    def get_stats(self) -> dict:
        """Get learning statistics"""
        return {
            'enabled': self.enabled,
            'threshold': self.threshold,
            'learned_count': self.learned_count,
            'max_references_per_product': self.max_refs
        }
