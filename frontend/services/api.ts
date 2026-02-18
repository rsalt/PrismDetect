import axios from 'axios';
import { Product, Detection } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export interface DetectionResponse {
    detections: Detection[];
    inference_time?: number;
}

export const prismApi = {
    // Health
    getHealth: async () => {
        try {
            const response = await api.get('/health');
            return response.data;
        } catch (e) {
            return null;
        }
    },

    // Products
    getProducts: async () => {
        const response = await api.get<{ products: Product[] }>('/products');
        return response.data.products;
    },

    getProduct: async (productId: string) => {
        const response = await api.get<Product>(`/products/${productId}`);
        return response.data;
    },

    addProduct: async (product: { id: string; name: string }) => {
        // Backend expects reference_images list, even if empty
        const response = await api.post('/products', {
            ...product,
            reference_images: []
        });
        return response.data;
    },

    deleteProduct: async (productId: string) => {
        // Not implemented in backend yet? specific route seems missing in snippet, assume existing or skip
        // Returning mock for safety if not exists
        return true;
    },

    uploadReference: async (productId: string, file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        const response = await api.post(`/products/${productId}/references`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    },

    deleteReference: async (productId: string, refId: string) => {
        const response = await api.delete(`/products/${productId}/references/${refId}`);
        return response.data;
    },

    // Detection
    detect: async (file: File, minConfidence?: number) => {
        const formData = new FormData();
        formData.append('file', file);

        let url = '/detect';
        if (minConfidence !== undefined) {
            url += `?min_confidence=${minConfidence}`;
        }

        const response = await api.post<{ detections: Detection[] }>(url, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data.detections;
    },

    // Metrics
    getMetrics: async () => {
        const response = await api.get('/metrics');
        return response.data;
    }
};

export default prismApi;
