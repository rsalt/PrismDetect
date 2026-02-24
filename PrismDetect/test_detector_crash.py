import sys
import numpy as np
import cv2

sys.path.append('.')
from core.detector import ProductDetector

detector = ProductDetector(config_path="config/products.json",
                           model_path="models/clip_int8.onnx",
                           index_path="data/index/product_index.faiss")

# Create a dummy image
img = np.random.randint(0, 256, (1000, 1000, 3), dtype=np.uint8)

print("Starting detection...")
try:
    results = detector.detect(img)
    print(f"Detection finished with {len(results)} results")
except Exception as e:
    print("Caught Exception:", e)
    import traceback
    traceback.print_exc()
