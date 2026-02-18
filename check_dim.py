import sys
import os
import numpy as np
import cv2

# Add project root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'PrismDetect'))

try:
    from PrismDetect.core.clip_onnx import ONNXCLIP
    
    print("Testing CLIP model dimension...")
    clip = ONNXCLIP(model_path="PrismDetect/models/clip_int8.onnx")
    
    # Create dummy image
    img = np.zeros((224, 224, 3), dtype=np.uint8)
    
    # Encode
    emb = clip.encode(img)
    
    print(f"Embedding shape: {emb.shape}")
    print(f"Dimension: {emb.shape[0]}")
    
except Exception as e:
    print(f"Error: {e}")
