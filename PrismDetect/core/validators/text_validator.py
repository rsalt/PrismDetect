"""
Text validator using EasyOCR
"""

import easyocr
import numpy as np
import cv2
from typing import List, Tuple
from loguru import logger

class TextValidator:
    """Validate product text using OCR"""
    
    def __init__(self, languages: List[str] = ['en']):
        """
        Initialize OCR reader
        
        Args:
            languages: List of language codes
        """
        try:
            self.reader = easyocr.Reader(
                languages,
                gpu=False,  # CPU-only for compatibility
                model_storage_directory='models/ocr',
                download_enabled=True
            )
            logger.info(f"✅ OCR initialized with languages: {languages}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize OCR (running in degraded mode): {e}")
            self.reader = None
    
    def extract_text(self, image: np.ndarray) -> List[dict]:
        """
        Extract text from image
        
        Args:
            image: BGR image
            
        Returns:
            List of detected text with confidence
        """
        if self.reader is None:
            return []
            
        # Convert BGR to RGB
        if len(image.shape) == 3 and image.shape[2] == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image
        
        try:
            # Run OCR
            results = self.reader.readtext(
                image_rgb,
                paragraph=False,
                width_ths=0.7,
                height_ths=0.7,
                decoder='beamsearch'
            )
            
            texts = []
            for (bbox, text, confidence) in results:
                texts.append({
                    'text': text,
                    'confidence': float(confidence),
                    'bbox': bbox
                })
            
            return texts
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return []
    
    def validate(self, image: np.ndarray, keywords: List[str]) -> Tuple[bool, List[str]]:
        """
        Validate if image contains brand keywords
        
        Args:
            image: BGR image
            keywords: List of brand keywords to look for
            
        Returns:
            Tuple of (is_valid, matched_keywords)
        """
        if not keywords:
            return True, []
        
        # Extract text
        texts = self.extract_text(image)
        
        # Combine all detected text
        detected_text = ' '.join([t['text'].lower() for t in texts])
        
        # Check for keywords
        matched = []
        for keyword in keywords:
            if keyword.lower() in detected_text:
                matched.append(keyword)
        
        is_valid = len(matched) > 0
        
        if is_valid:
            logger.debug(f"Text validation passed: found {matched}")
        else:
            logger.debug(f"Text validation failed: keywords {keywords} not in '{detected_text}'")
        
        return is_valid, matched
    
    def get_text_regions(self, image: np.ndarray) -> List[np.ndarray]:
        """
        Get cropped regions containing text
        
        Args:
            image: BGR image
            
        Returns:
            List of text region images
        """
        if self.reader is None:
            return []
            
        results = self.reader.readtext(image)
        
        regions = []
        for (bbox, text, confidence) in results:
            # Convert bbox points to rectangle
            pts = np.array(bbox, dtype=np.int32)
            x = min(pts[:, 0])
            y = min(pts[:, 1])
            w = max(pts[:, 0]) - x
            h = max(pts[:, 1]) - y
            
            # Add padding
            pad = 10
            x = max(0, x - pad)
            y = max(0, y - pad)
            w = min(image.shape[1] - x, w + 2*pad)
            h = min(image.shape[0] - y, h + 2*pad)
            
            if w > 0 and h > 0:
                region = image[y:y+h, x:x+w]
                regions.append(region)
        
        return regions
