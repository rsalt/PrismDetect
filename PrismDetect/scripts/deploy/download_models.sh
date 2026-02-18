#!/bin/bash
# download_models.sh - Download pre-built models for production

set -e

echo "📥 Downloading pre-built models..."

# Create models directory
mkdir -p models

# Model URLs (replace with your CDN/bucket)
BASE_URL="https://your-cdn.com/models"

# Detect platform
OS=$(uname -s)
ARCH=$(uname -m)

echo "Platform: $OS-$ARCH"

# Check if model already exists (e.g. copied from host)
if [ -f "models/clip_int8.onnx" ]; then
    echo "✅ Model already exists, skipping download."
    exit 0
fi

# Function to download with python (since curl might be missing)
download() {
    url=$1
    dest=$2
    echo "Downloading $url to $dest..."
    python3 -c "import urllib.request; urllib.request.urlretrieve('$url', '$dest')"
}

# Download appropriate model
if [ "$OS" = "Darwin" ] && [ "$ARCH" = "arm64" ]; then
    # Mac Apple Silicon
    echo "🍎 Downloading ONNX model for Mac..."
    download "$BASE_URL/clip_int8.onnx" "models/clip_int8.onnx"
    
elif [ "$OS" = "Linux" ] && [ "$ARCH" = "x86_64" ]; then
    # Linux x86_64
    echo "🐧 Downloading ONNX model for Linux..."
    download "$BASE_URL/clip_int8.onnx" "models/clip_int8.onnx"
    
elif [ "$OS" = "Linux" ] && [[ "$ARCH" == "arm"* || "$ARCH" == "aarch64" ]]; then
    # ARM
    echo "📱 Downloading ONNX model for ARM..."
    download "$BASE_URL/clip_int8_arm.onnx" "models/clip_int8.onnx"
    
else
    # Fallback
    echo "⚠️ Unknown platform, downloading generic ONNX model..."
    download "$BASE_URL/clip_int8.onnx" "models/clip_int8.onnx"
fi

# Verify download
if [ -f "models/clip_int8.onnx" ]; then
    SIZE=$(du -h models/clip_int8.onnx | cut -f1)
    echo "✅ Model downloaded: $SIZE"
else
    echo "❌ Download failed"
    exit 1
fi

# Download test image (optional)
mkdir -p tests/fixtures/test_images
# Check if test image exists
if [ ! -f "tests/fixtures/test_images/test_milk.jpg" ]; then
    echo "Downloading test image..."
    # Use python for test image too
    python3 -c "import urllib.request; urllib.request.urlretrieve('https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Milk_glass.jpg/440px-Milk_glass.jpg', 'tests/fixtures/test_images/test_milk.jpg')" || echo "⚠️ Test image download failed"
fi

echo "✅ Setup complete!"
