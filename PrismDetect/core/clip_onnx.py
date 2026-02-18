"""
Unified ONNX CLIP model - Single backend for all platforms
"""

import onnxruntime as ort
import numpy as np
import cv2
from pathlib import Path
from loguru import logger

class ONNXCLIP:
    """Single universal CLIP implementation using ONNX Runtime"""
    
    def __init__(self, model_path: str = "models/clip_int8.onnx"):
        """Initialize ONNX CLIP model"""
        
        if not Path(model_path).exists():
            raise FileNotFoundError(
                f"Model not found at {model_path}. "
                "Run 'scripts/deploy/download_models.sh' first."
            )
        
        # Load model with available providers
        available_providers = ort.get_available_providers()
        providers = []
        
        # Prioritize GPU providers
        if 'CUDAExecutionProvider' in available_providers:
            providers.append('CUDAExecutionProvider')
        if 'CoreMLExecutionProvider' in available_providers:
            providers.append('CoreMLExecutionProvider')
            
        # Always fallback to CPU
        providers.append('CPUExecutionProvider')
        
        logger.info(f"Available ONNX providers: {available_providers}")
        logger.info(f"Selected providers: {providers}")
        
        self.session = ort.InferenceSession(
            model_path,
            providers=providers
        )
        
        # ImageNet normalization values for CLIP
        self.mean = np.array([0.48145466, 0.4578275, 0.40821073])
        self.std = np.array([0.26862954, 0.26130258, 0.27577711])
        
        # Get input/output details
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        self.input_shape = self.session.get_inputs()[0].shape
        
        logger.info(f"✅ ONNX CLIP loaded: {Path(model_path).name}")
        logger.info(f"   Input: {self.input_name} {self.input_shape}")
        logger.info(f"   Output: {self.output_name}")
        logger.info(f"   Providers: {self.session.get_providers()}")
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for CLIP model
        
        Args:
            image: BGR image (H, W, C)
            
        Returns:
            Preprocessed tensor (1, 3, 224, 224)
        """
        # Resize to 224x224 with padding (Letterboxing) to preserve aspect ratio
        h, w = image.shape[:2]
        target_size = 224
        
        # Calculate scaling factor
        scale = min(target_size / h, target_size / w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # Resize maintaining aspect ratio
        resized = cv2.resize(image, (new_w, new_h))
        
        # Create square canvas
        canvas = np.zeros((target_size, target_size, 3), dtype=np.uint8)
        
        # Center the image
        x_offset = (target_size - new_w) // 2
        y_offset = (target_size - new_h) // 2
        canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
        
        image = canvas
        
        # Convert BGR to RGB
        if len(image.shape) == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Normalize to [0, 1]
        image = image.astype(np.float32) / 255.0
        
        # Apply CLIP normalization
        image = (image - self.mean) / self.std
        
        # Convert to NCHW format
        image = image.transpose(2, 0, 1)
        image = np.expand_dims(image, axis=0)
        
        return image.astype(np.float32)
    
    def encode(self, image: np.ndarray) -> np.ndarray:
        """
        Encode image to embedding vector
        
        Args:
            image: BGR image
            
        Returns:
            Normalized embedding vector (512-dim)
        """
        # Preprocess
        inputs = self.preprocess(image)
        
        # Run inference
        outputs = self.session.run(
            [self.output_name],
            {self.input_name: inputs}
        )[0]
        
        # Get embedding
        if len(outputs.shape) == 3:
            # (Batch, Seq, Dim) -> Take CLS token at index 0
            embedding = outputs[:, 0, :].flatten()
        else:
            # Already pooled or flat
            embedding = outputs.flatten()
            
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding.astype(np.float32)
    
    def encode_batch(self, images: list) -> np.ndarray:
        """
        Encode multiple images in batch
        
        Args:
            images: List of BGR images
            
        Returns:
            Batch of embeddings (N, 512)
        """
        # Preprocess all images
        batch = []
        for img in images:
            batch.append(self.preprocess(img)[0])
        
        # Stack into batch
        batch = np.stack(batch, axis=0)
        
        # Run inference
        outputs = self.session.run(
            [self.output_name],
            {self.input_name: batch}
        )[0]
        
        # Normalize each embedding
        for i in range(outputs.shape[0]):
            norm = np.linalg.norm(outputs[i])
            if norm > 0:
                outputs[i] = outputs[i] / norm
        
        return outputs.astype(np.float32)
