"""
Shape validator using aspect ratio analysis
"""

import cv2
import numpy as np
from loguru import logger

class ShapeValidator:
    """Validate product shape using aspect ratio"""
    
    @staticmethod
    def get_aspect_ratio(image: np.ndarray) -> float:
        """
        Extract aspect ratio of main object in image
        
        Args:
            image: BGR image
            
        Returns:
            Aspect ratio (width/height)
        """
        h, w = image.shape[:2]
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Edge detection
        edges = cv2.Canny(blurred, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(
            edges, 
            cv2.RETR_EXTERNAL, 
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        if contours:
            # Get largest contour (assumed to be main object)
            main_contour = max(contours, key=cv2.contourArea)
            
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(main_contour)
            
            if h > 0:
                return w / h
        
        # Fallback to full image ratio
        return w / h if h > 0 else 1.0
    
    @staticmethod
    def validate(actual_ratio: float, expected_ratio: float, 
                tolerance: float = 0.15) -> bool:
        """
        Check if aspect ratio matches within tolerance
        
        Args:
            actual_ratio: Detected aspect ratio
            expected_ratio: Expected aspect ratio from reference
            tolerance: Allowed deviation (e.g., 0.15 = ±15%)
            
        Returns:
            True if shape is valid
        """
        if expected_ratio <= 0:
            return True  # Skip validation if no expected ratio
        
        min_ratio = expected_ratio * (1 - tolerance)
        max_ratio = expected_ratio * (1 + tolerance)
        
        is_valid = min_ratio <= actual_ratio <= max_ratio
        
        logger.debug(f"Shape validation: {actual_ratio:.2f} vs {expected_ratio:.2f} "
                    f"(±{tolerance*100:.0f}%) = {is_valid}")
        
        return is_valid
    
    @staticmethod
    def get_shape_descriptors(image: np.ndarray) -> dict:
        """
        Extract multiple shape descriptors
        
        Args:
            image: BGR image
            
        Returns:
            Dictionary of shape metrics
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return {}
        
        main_contour = max(contours, key=cv2.contourArea)
        
        # Calculate various shape metrics
        area = cv2.contourArea(main_contour)
        perimeter = cv2.arcLength(main_contour, True)
        x, y, w, h = cv2.boundingRect(main_contour)
        
        # Hu moments (shape invariants)
        moments = cv2.moments(main_contour)
        hu_moments = cv2.HuMoments(moments).flatten()
        
        return {
            'aspect_ratio': w / h if h > 0 else 1.0,
            'area': float(area),
            'perimeter': float(perimeter),
            'extent': float(area / (w * h)) if w * h > 0 else 0,
            'hu_moments': hu_moments.tolist()
        }
