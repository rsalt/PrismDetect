#!/usr/bin/env python3
"""
Build ONNX model from CLIP
Run this on a machine with 4GB+ RAM (not on production)
"""

import torch
import onnx
import onnxoptimizer
from onnxruntime.quantization import quantize_dynamic, QuantType
from transformers import CLIPModel
import numpy as np
from pathlib import Path

def build_onnx_model():
    """Build and optimize ONNX model"""
    
    print("🚀 Building ONNX model from CLIP...")
    
    # Create models directory
    Path("models").mkdir(exist_ok=True)
    
    # Load CLIP model
    print("📥 Loading CLIP model...")
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    model.eval()
    
    # Create dummy input
    dummy_input = torch.randn(1, 3, 224, 224)
    
    # Export to ONNX
    print("📤 Exporting to ONNX...")
    torch.onnx.export(
        model.vision_model,
        dummy_input,
        "models/clip_raw.onnx",
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=['pixel_values'],
        output_names=['image_embeds'],
        dynamic_axes={
            'pixel_values': {0: 'batch_size'},
            'image_embeds': {0: 'batch_size'}
        }
    )
    
    # Optimize ONNX
    print("⚡ Optimizing ONNX...")
    onnx_model = onnx.load("models/clip_raw.onnx")
    optimized = onnxoptimizer.optimize(onnx_model)
    onnx.save(optimized, "models/clip_optimized.onnx")
    
    # Quantize to INT8
    print("🔧 Quantizing to INT8...")
    quantize_dynamic(
        "models/clip_optimized.onnx",
        "models/clip_int8.onnx",
        weight_type=QuantType.QUInt8
    )
    
    # Cleanup
    Path("models/clip_raw.onnx").unlink()
    
    # Verify
    import onnxruntime as ort
    session = ort.InferenceSession("models/clip_int8.onnx")
    
    print("\n✅ Model built successfully!")
    print(f"   Input: {session.get_inputs()[0].name} {session.get_inputs()[0].shape}")
    print(f"   Output: {session.get_outputs()[0].name}")
    print(f"   Size: {Path('models/clip_int8.onnx').stat().st_size / 1024 / 1024:.1f}MB")
    print(f"   Providers: {session.get_providers()}")
    
    # Test inference
    test_input = np.random.randn(1, 3, 224, 224).astype(np.float32)
    output = session.run(None, {'pixel_values': test_input})
    print(f"   Test output shape: {output[0].shape}")

if __name__ == "__main__":
    build_onnx_model()
