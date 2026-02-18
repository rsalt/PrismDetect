#!/usr/bin/env python3
"""
Test detection on sample images
"""

import sys
from pathlib import Path
import cv2
import json
from pprint import pprint

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.detector import ProductDetector

def test_detection(image_path: str):
    """Test detection on a single image"""
    
    print(f"\n🔍 Testing detection on: {image_path}")
    
    # Initialize detector
    detector = ProductDetector()
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Could not load image: {image_path}")
        return
    
    # Run detection
    results = detector.detect(image)
    
    # Print results
    print(f"\n📊 Found {len(results)} detections:")
    for i, result in enumerate(results, 1):
        print(f"\n  {i}. {result.product_name}")
        print(f"     Confidence: {result.confidence:.3f}")
        print(f"     Text verified: {result.text_verified}")
        print(f"     Shape valid: {result.shape_valid}")
        if result.matched_keywords:
            print(f"     Keywords: {', '.join(result.matched_keywords)}")
        print(f"     BBox: {result.bbox}")
    
    return results

def batch_test():
    """Test multiple images"""
    test_dir = Path("tests/fixtures/test_images")
    
    if not test_dir.exists():
        print(f"❌ Test directory not found: {test_dir}")
        return
    
    for img_path in test_dir.glob("*.jpg"):
        test_detection(str(img_path))
        print("-" * 50)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_detection(sys.argv[1])
    else:
        batch_test()
