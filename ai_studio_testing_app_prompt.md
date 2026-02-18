# Prompt for Google AI Studio: PrismDetect Testing Application

**Goal:** Create a comprehensive testing and management dashboard for the "PrismDetect" API.
**Tech Stack:** Python (Streamlit) OR React (Vite + Tailwind). Streamlit is preferred for rapid prototyping and data visualization.

## 1. Context
PrismDetect is an AI-based product detection system running on `http://localhost:8000`. It uses CLIP embeddings and Vector Search to identify products in images.
We need a frontend application to test the full lifecycle: Adding products, uploading reference images, and running detections on new images.

## 2. API Specification
The application should interact with the following endpoints:

### System
- `GET /health`: Returns system status (CPU, Memory) and model info.
- `GET /metrics`: Returns Prometheus metrics (detection_latency, request_count).

### Product Management
- `GET /products`: Returns a list of all configured products.
  - Response: `[{"id": "coke_can", "name": "Coke Can", "reference_count": 5}, ...]`
- `POST /products`: Creates a new product.
  - Body: `{"id": "new_product", "name": "New Product"}`
- `DELETE /products/{product_id}`: Deletes a product.
- `POST /products/{product_id}/references`: Uploads a reference image.
  - Body: `multipart/form-data` with key `file`.

### Detection
- `POST /detect`: Detects products in an uploaded image.
  - Body: `multipart/form-data` with key `file`.
  - Response:
    ```json
    {
      "detections": [
        {
          "product_id": "coke_can",
          "confidence": 0.92,
          "box": [50, 50, 200, 300], // [x1, y1, x2, y2]
          "processing_time": 0.15
        }
      ],
      "inference_time": 0.15
    }
    ```

## 3. Required Features

### A. Dashboard (Home)
- Display system health status (Green/Red indicator).
- Show Total Products and Total References count.
- Visualize simple metrics if available (e.g., average latency).

### B. Product Manager
- **List View**: Table showing all products with their ID, Name, and Reference Count.
- **Add Product**: Form to input ID and Name to create a new product.
- **Manage References**: Click on a product to see its details. reliable upload button to add new reference images to that product.

### C. Detection Playground (The Core Feature)
- **Image Upload**: Drag-and-drop area for testing images.
- **Visualization**: When an image is uploaded and processed:
  - Draw bounding boxes around detected products.
  - Label boxes with `Product Name (Confidence %)`.
  - Use different colors for different product IDs.
- **JSON View**: Toggle to show the raw JSON response for debugging.

### D. Batch Testing (Optional)
- Allow uploading multiple images.
- Display a summary table of results: Image Name | Detected Products | Max Confidence.

## 4. Design Requirements
- Clean, modern UI (Dark mode preferred).
- Responsive layout.
- Error handling: Show toast notifications if API calls fail.
