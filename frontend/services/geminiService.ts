
import { GoogleGenAI, Type } from "@google/genai";
import { Detection } from "../types";

export async function detectObjects(imageBuffer: string): Promise<{ detections: Detection[], latency: number }> {
  // Always use process.env.API_KEY directly when initializing.
  const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
  const startTime = Date.now();
  
  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: {
        parts: [
          { text: "Detect objects in this image and return them as a JSON list. For each object include label, confidence (0 to 1), and box_2d as [ymin, xmin, ymax, xmax] in normalized coordinates from 0 to 1000." },
          { inlineData: { mimeType: 'image/jpeg', data: imageBuffer.split(',')[1] } }
        ]
      },
      config: {
        responseMimeType: 'application/json',
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            detections: {
              type: Type.ARRAY,
              items: {
                type: Type.OBJECT,
                properties: {
                  label: { type: Type.STRING },
                  confidence: { type: Type.NUMBER },
                  box_2d: {
                    type: Type.ARRAY,
                    items: { type: Type.NUMBER }
                  }
                },
                required: ['label', 'confidence', 'box_2d']
              }
            }
          }
        }
      }
    });

    const endTime = Date.now();
    const data = JSON.parse(response.text || '{"detections": []}');
    
    return {
      detections: data.detections.map((d: any) => ({
        ...d,
        id: Math.random().toString(36).substring(7)
      })),
      latency: endTime - startTime
    };
  } catch (error) {
    console.error("Gemini Detection Error:", error);
    throw error;
  }
}
