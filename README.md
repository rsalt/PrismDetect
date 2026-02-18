# 🚀 PrismDetect

Lightweight AI-based product detection system that identifies products through multi-stage validation: visual similarity + text verification + shape analysis.

## ✨ Features

- **No training required** - Just upload reference images
- **Patch scanning** - Finds products even in complex scenes
- **3-stage validation** - Near-zero false positives
- **Self-learning** - Improves automatically over time
- **33MB model** - Runs anywhere (EC2, Mac Mini, Raspberry Pi)
- **80-100MB RAM** - Runs on 1GB VMs
- **FAISS indexing** - Scales to millions of products
- **ONNX Runtime** - Single backend for all platforms

## 🏗️ Architecture
Input Image → Patch Scanner → ONNX CLIP → FAISS Search → OCR + Shape → Decision

## 📋 Requirements

- Python 3.9+
- 1GB RAM minimum (2GB recommended)
- 100MB disk space

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/yourusername/prismdetect.git
cd prismdetect

# Install
make install

# Download model
make download-models

# Run
make run
```

## 📦 Docker Deployment
```bash
# Build and run with Docker Compose
make docker-up

# API available at http://localhost:8000
```

## 📖 API Documentation
Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Detect Product
```bash
curl -X POST "http://localhost:8000/detect" \
  -H "accept: application/json" \
  -F "file=@milk_bottle.jpg"
```

### Add Product
```bash
curl -X POST "http://localhost:8000/products" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "new_product",
    "name": "New Product",
    "keywords": ["brand", "product"],
    "reference_images": [
      {"id": "ref1", "url": "data/references/new_product/ref1.jpg"}
    ]
  }'
```
