"""
Sliding window patch scanner - Critical for finding products in complex scenes
"""

import cv2
import numpy as np
from typing import List, Tuple
from loguru import logger

class PatchScanner:
    """Sliding window patch scanner"""
    
    def __init__(self, patch_size: int = 224, stride: int = 112):
        """
        Initialize patch scanner
        
        Args:
            patch_size: Size of square patches
            stride: Step size between patches (smaller = more patches)
        """
        self.patch_size = patch_size
        self.stride = stride
        logger.debug(f"Patch scanner: size={patch_size}, stride={stride}")
    
    def scan(self, image: np.ndarray) -> List[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
        """
        Scan image with sliding window
        
        Args:
            image: BGR image
            
        Returns:
            List of (patch, (x, y, w, h))
        """
        h, w = image.shape[:2]
        patches = []
        
        # Ensure image is at least patch size
        if h < self.patch_size or w < self.patch_size:
            # Pad image if too small
            pad_h = max(0, self.patch_size - h)
            pad_w = max(0, self.patch_size - w)
            image = cv2.copyMakeBorder(
                image, 
                0, pad_h, 0, pad_w,
                cv2.BORDER_REPLICATE
            )
            h, w = image.shape[:2]
        
        # Calculate number of patches
        num_y = max(1, (h - self.patch_size) // self.stride + 1)
        num_x = max(1, (w - self.patch_size) // self.stride + 1)
        
        # Generate regular grid patches
        for y in range(0, h - self.patch_size + 1, self.stride):
            for x in range(0, w - self.patch_size + 1, self.stride):
                patch = image[y:y+self.patch_size, x:x+self.patch_size]
                patches.append((patch, (x, y, self.patch_size, self.patch_size)))
        
        # Add multi-scale patches (50%, 75%, 125% scales)
        scales = [0.5, 0.75, 1.25]
        for scale in scales:
            if scale == 1.0:
                continue
                
            new_size = int(self.patch_size * scale)
            if new_size < 64 or new_size > min(h, w):
                continue
            
            # Resize image for this scale
            scaled = cv2.resize(image, (int(w*scale), int(h*scale)))
            sh, sw = scaled.shape[:2]
            
            if sh >= new_size and sw >= new_size:
                for y in range(0, sh - new_size + 1, self.stride):
                    for x in range(0, sw - new_size + 1, self.stride):
                        patch = scaled[y:y+new_size, x:x+new_size]
                        # Map back to original coordinates
                        orig_x = int(x / scale)
                        orig_y = int(y / scale)
                        orig_w = int(new_size / scale)
                        orig_h = int(new_size / scale)
                        patches.append((patch, (orig_x, orig_y, orig_w, orig_h)))
        
        # Add center crop (important for full image context)
        center_x = max(0, (w - self.patch_size) // 2)
        center_y = max(0, (h - self.patch_size) // 2)
        center_patch = image[center_y:center_y+self.patch_size, 
                            center_x:center_x+self.patch_size]
        patches.append((center_patch, (center_x, center_y, self.patch_size, self.patch_size)))

        # Add full image context (Global View)
        # Resize entire image to patch_size to capture global context
        try:
            full_resized = cv2.resize(image, (self.patch_size, self.patch_size))
            patches.append((full_resized, (0, 0, w, h)))
        except Exception as e:
            logger.warning(f"Could not add full image context: {e}")
        
        logger.debug(f"Generated {len(patches)} patches from {w}x{h} image")
        return patches
    
    def scan_with_overlap(self, image: np.ndarray, overlap_ratio: float = 0.5) -> List[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
        """
        Scan with specific overlap ratio
        
        Args:
            image: BGR image
            overlap_ratio: Overlap between patches (0-1)
            
        Returns:
            List of patches
        """
        stride = int(self.patch_size * (1 - overlap_ratio))
        self.stride = stride
        return self.scan(image)
