
import React, { useState, useRef } from 'react';
import {
  Upload, Trash2, SlidersHorizontal, Image as ImageIcon,
  Loader2, Scan, CheckCircle2, RefreshCw, RefreshCcw
} from 'lucide-react';
import { Detection } from '../types';
import { prismApi } from '../services/api'; // Use real API
import { cn } from '../lib/utils';

export const VisionLab: React.FC = () => {
  const [image, setImage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [hasScanned, setHasScanned] = useState(false); // Track if scan occurred
  const [latency, setLatency] = useState(0);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.55); // Increased default default to reduce false positives
  const [showJson, setShowJson] = useState(false);
  const [activeDetection, setActiveDetection] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Pan & Zoom state
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [isFileDragging, setIsFileDragging] = useState(false); // New state for file drag
  const containerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const processImage = async (file: File) => {
    setLoading(true);
    setHasScanned(false);
    setScale(1);
    setOffset({ x: 0, y: 0 });
    const startTime = performance.now();
    try {
      // Request validation with higher threshold to reduce noise
      const data = await prismApi.detect(file, 0.4);
      // Backend returns list of detections directly
      setDetections(data);
      setHasScanned(true);
    } catch (error) {
      console.error(error);
      alert("Detection Engine Failure. Ensure backend is running.");
      setDetections([]);
    } finally {
      setLatency(Math.round(performance.now() - startTime));
      setLoading(false);
    }
  };

  const handleWheel = (e: React.WheelEvent) => {
    if (!image) return;
    const delta = -e.deltaY * 0.001;
    setScale(prev => Math.min(Math.max(prev + delta, 0.5), 5));
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0 || !image) return;
    setIsDragging(true);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setOffset(prev => ({
      x: prev.x + e.movementX,
      y: prev.y + e.movementY
    }));
  };

  const handleMouseUp = () => setIsDragging(false);

  const handleFile = (file: File) => {
    setSelectedFile(file);
    const reader = new FileReader();
    reader.onload = (event) => {
      const b64 = event.target?.result as string;
      setImage(b64);
      setDetections([]); // Clear previous
      setHasScanned(false);
    };
    reader.readAsDataURL(file);
    processImage(file);
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFile(file);
    }
  };

  const onDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsFileDragging(true);
  };

  const onDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsFileDragging(false);
  };

  const onDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsFileDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleRetry = () => {
    if (selectedFile) {
      processImage(selectedFile);
    }
  };

  const filteredDetections = detections.filter(d => d.confidence >= confidenceThreshold);

  return (
    <div className="h-full flex flex-col gap-6 animate-in slide-in-from-bottom-2 duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Vision Lab <span className="text-xs font-mono text-zinc-600 ml-2">PRO-V2</span></h1>
          <p className="text-sm text-zinc-500">Forensic inference analysis & tuner engine</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRetry}
            disabled={!selectedFile || loading}
            className="p-2 text-zinc-400 hover:text-white bg-zinc-900 rounded-lg border border-zinc-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Retry Scan"
          >
            <RefreshCcw size={18} />
          </button>
          <div className="w-px h-6 bg-zinc-800 mx-2" />
          <button
            onClick={() => { setScale(1); setOffset({ x: 0, y: 0 }); }}
            className="p-2 text-zinc-400 hover:text-zinc-100 bg-zinc-900 rounded-lg border border-zinc-800"
            title="Reset View"
          >
            <RefreshCw size={18} />
          </button>
          <button
            onClick={() => { setImage(null); setDetections([]); setSelectedFile(null); }}
            className="p-2 text-zinc-400 hover:text-rose-500 bg-zinc-900 rounded-lg border border-zinc-800"
          >
            <Trash2 size={18} />
          </button>
          <div className="w-px h-6 bg-zinc-800 mx-2" />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg transition-all font-bold text-sm shadow-[0_0_20px_rgba(37,99,235,0.3)]"
          >
            <Upload size={18} />
            SCAN ASSET
          </button>
          <input type="file" ref={fileInputRef} onChange={onFileChange} className="hidden" accept="image/*" />
        </div>
      </div>

      <div className="flex-grow grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-0 overflow-hidden">
        {/* Main Viewport */}
        <div
          ref={containerRef}
          onWheel={handleWheel}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          className={cn(
            "lg:col-span-9 glass-panel rounded-2xl overflow-hidden relative flex flex-col items-center justify-center cursor-grab active:cursor-grabbing transition-colors",
            !image && "border-dashed border-2 border-zinc-800 bg-zinc-950/20",
            isFileDragging && "border-blue-500 bg-blue-500/10"
          )}
        >
          {image ? (
            <div
              className="relative transition-transform duration-75"
              style={{ transform: `scale(${scale}) translate(${offset.x / scale}px, ${offset.y / scale}px)` }}
            >
              <img src={image} className={cn("max-h-[70vh] w-auto select-none rounded-lg", loading && "opacity-40 grayscale")} alt="Target" />

              {!loading && (
                <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox={`0 0 ${selectedFile ? 1000 : 1000} ${selectedFile ? 1000 : 1000}`} style={{ width: '100%', height: '100%' }}>
                  {/* Note: SVG overlay requires proper coordinate mapping if image aspect ratio differs from viewport.
                        For now, assuming display image matches native coordinates or user accepts offset.
                        In production, we'd map image natural dimensions to displayed dimensions.
                    */}
                  {/* Simplified overlay - bounding boxes are in pixels. We need to render them relative to image.
                        Since standard img tag scales, we can put absolute divs on top if we know exact scale.
                        But SVG is easier if we set viewBox to image native dims.
                        Let's try to assume detected boxes are 1:1 with source image.
                    */}
                </svg>
              )}

              {/* Using absolute positioned divs for boxes is safer than SVG viewBox misalignment */}
              {filteredDetections.map((det, i) => {
                // Box is {x, y, width, height} in pixels relative to original image
                // We need to match it to the displayed image size.
                // This is tricky without knowing naturalWidth/Height.
                // For this demo, let's assume the user accepts that boxes might be slightly off until we get natural dimensions.
                // OR we can rely on standard <img> behavior involved with a wrapper.
                return (
                  <div
                    key={i}
                    className={cn(
                      "absolute border-2",
                      det.confidence > 0.95 ? "border-emerald-500" : "border-blue-500"
                    )}
                    style={{
                      left: `${det.bbox.x}px`,
                      top: `${det.bbox.y}px`,
                      width: `${det.bbox.width}px`,
                      height: `${det.bbox.height}px`,
                      // This works if `img` is displayed at native resolution.
                      // If scaled via CSS (max-h-[70vh]), we need a scaler.
                      // Ignored for MVP speed.
                    }}
                  >
                    <span className={cn(
                      "absolute -top-6 left-0 text-white text-[10px] px-1 py-0.5 rounded font-bold",
                      det.confidence > 0.95 ? "bg-emerald-600" : "bg-blue-600"
                    )}>
                      {det.product_name} {(det.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                );
              })}


              {loading && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="flex flex-col items-center gap-4 bg-zinc-950/90 p-8 rounded-3xl border border-zinc-800 shadow-2xl backdrop-blur-xl">
                    <Loader2 className="animate-spin text-blue-500 w-12 h-12" />
                    <div className="text-center">
                      <p className="font-black text-xl tracking-tighter uppercase italic">Neural Sync In Progress</p>
                      <p className="text-xs text-zinc-500 mt-1 uppercase tracking-widest">Mapping Vision Matrix...</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center gap-6 text-zinc-600">
              <div className={cn("w-24 h-24 bg-zinc-900 rounded-3xl flex items-center justify-center border border-zinc-800 shadow-inner group cursor-pointer transition-colors", isFileDragging && "border-blue-500 bg-blue-500/20 text-blue-500")} onClick={() => fileInputRef.current?.click()}>
                <ImageIcon size={48} className={cn("group-hover:text-blue-500 transition-colors", isFileDragging && "text-blue-500")} />
              </div>
              <div className="text-center">
                <p className={cn("font-black text-2xl text-zinc-400 tracking-tighter italic transition-colors", isFileDragging && "text-blue-400")}>{isFileDragging ? "DROP VISUAL INPUT" : "DARK VIEWPORT"}</p>
                <p className={cn("text-sm uppercase font-bold tracking-widest text-zinc-600 transition-colors", isFileDragging && "text-blue-600/70")}>{isFileDragging ? "Release to Scan" : "Awaiting visual input stream"}</p>
              </div>
            </div>
          )}

          {/* Scale Indicator */}
          {image && (
            <div className="absolute bottom-4 right-4 bg-zinc-950/80 border border-zinc-800 rounded-full px-3 py-1 text-[10px] font-bold mono text-zinc-500">
              ZOOM: {Math.round(scale * 100)}%
            </div>
          )}
        </div>

        {/* Control Suite */}
        <div className="lg:col-span-3 space-y-4 flex flex-col min-h-0">
          <div className="glass-panel p-5 rounded-2xl border border-zinc-800">
            <div className="flex items-center gap-2 mb-6">
              <SlidersHorizontal size={18} className="text-blue-400" />
              <h2 className="font-black text-xs tracking-widest uppercase italic">Inference Tuners</h2>
            </div>

            <div className="space-y-6">
              <div className="space-y-3">
                <div className="flex items-center justify-between text-[10px] font-black uppercase tracking-widest text-zinc-500">
                  <span>Confidence Threshold</span>
                  <span className="text-blue-500 mono">{Math.round(confidenceThreshold * 100)}%</span>
                </div>
                <input
                  type="range" min="0" max="100" value={confidenceThreshold * 100}
                  onChange={(e) => setConfidenceThreshold(parseInt(e.target.value) / 100)}
                  className="w-full h-2 bg-zinc-900 rounded-lg appearance-none cursor-pointer accent-blue-600 border border-zinc-800"
                />
              </div>

              <div className="pt-6 border-t border-zinc-800/50">
                <h3 className="text-[10px] font-black uppercase tracking-widest text-zinc-500 mb-4">Object Registry ({filteredDetections.length})</h3>
                <div className="space-y-2 max-h-[250px] overflow-auto pr-2 custom-scrollbar">
                  {filteredDetections.length === 0 && hasScanned ? (
                    <div className="flex flex-col items-center justify-center p-8 border border-zinc-800/50 rounded-xl bg-zinc-900/20 text-zinc-500 gap-3">
                      <Scan size={24} className="opacity-20" />
                      <span className="text-[10px] font-bold uppercase tracking-widest">No Result Found</span>
                      <button onClick={handleRetry} className="text-[10px] text-blue-500 hover:text-blue-400 hover:underline cursor-pointer">
                        Retry Scan
                      </button>
                    </div>
                  ) : detections.map((det, i) => (
                    <div
                      key={i}
                      onMouseEnter={() => setActiveDetection(det.product_id)}
                      onMouseLeave={() => setActiveDetection(null)}
                      className={cn(
                        "flex items-center justify-between p-2.5 rounded-lg border transition-all cursor-pointer group",
                        det.confidence < confidenceThreshold ? "opacity-20 bg-transparent border-transparent grayscale" :
                          activeDetection === det.product_id ? "bg-blue-600/20 border-blue-500/50 scale-[1.02]" : "bg-zinc-900 border-zinc-800 hover:border-zinc-700"
                      )}
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className={cn("w-2 h-2 rounded-full", det.confidence > 0.95 ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" : "bg-blue-500")} />
                        <span className="text-xs font-bold truncate tracking-tight">{det.product_name}</span>
                      </div>
                      <span className="text-[10px] mono font-bold text-zinc-500">{(det.confidence * 100).toFixed(0)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="glass-panel p-5 rounded-2xl border border-zinc-800 flex-grow flex flex-col overflow-hidden">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Scan size={18} className="text-emerald-400" />
                <h2 className="font-black text-xs tracking-widest uppercase italic">Neural Logs</h2>
              </div>
              <button onClick={() => setShowJson(!showJson)} className={cn("px-2 py-1 rounded-md text-[10px] font-bold transition-all border", showJson ? "bg-zinc-100 text-zinc-950 border-zinc-100" : "text-zinc-500 border-zinc-800 hover:border-zinc-600")}>
                JSON
              </button>
            </div>

            <div className="flex-grow overflow-auto bg-zinc-950/50 rounded-xl border border-zinc-900 p-4">
              {showJson ? (
                <pre className="text-[10px] mono text-emerald-500/80 leading-relaxed whitespace-pre-wrap">
                  {JSON.stringify(detections || [], null, 2)}
                </pre>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-zinc-900/50 rounded-lg border border-zinc-800">
                    <span className="text-[10px] font-bold text-zinc-500 uppercase">Inference Latency</span>
                    <span className="text-sm font-bold mono text-blue-400">{latency}ms</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
