
export enum View {
  DASHBOARD = 'DASHBOARD',
  PRODUCT_STUDIO = 'PRODUCT_STUDIO',
  VISION_LAB = 'VISION_LAB',
  BATCH_FORENSICS = 'BATCH_FORENSICS',
  SETTINGS = 'SETTINGS'
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface Detection {
  product_id: string;
  product_name: string;
  confidence: number;
  bbox: BoundingBox;
  text_verified: boolean;
  shape_valid: boolean;
  processing_ms: number;
  matched_keywords?: string[];
}

export interface Product {
  id: string;
  name: string;
  active: boolean;
  reference_count: number;
  keywords: string[];
  created_at?: string;
  reference_images?: {
    id: string;
    url: string;
    angle?: string;
    added_at: number;
  }[];
}

export interface MetricPoint {
  time: string;
  latency: number;
  throughput: number;
}

export interface BatchItem {
  id: string;
  name: string;
  thumbnail: string;
  topDetection: string;
  confidence: number;
  latency: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
}
