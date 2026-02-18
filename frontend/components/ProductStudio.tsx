import React, { useState, useEffect, useRef } from 'react';
import {
  Plus, Search, Filter, Grid2X2, List,
  PackageCheck, X, Image as ImageIcon,
  History, ShieldCheck, MoreVertical, Trash2,
  Crop, Check
} from 'lucide-react';
import ReactCrop, { type Crop as CropType, PixelCrop, centerCrop, makeAspectCrop } from 'react-image-crop';
import 'react-image-crop/dist/ReactCrop.css';

function centerAspectCrop(mediaWidth: number, mediaHeight: number) {
  return centerCrop(
    makeAspectCrop(
      {
        unit: '%',
        width: 90,
      },
      undefined, // aspect
      mediaWidth,
      mediaHeight,
    ),
    mediaWidth,
    mediaHeight,
  )
}

import { Product } from '../types';
import { cn } from '../lib/utils';
import { prismApi } from '../services/api';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const ProductStudio: React.FC = () => {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [searchTerm, setSearchTerm] = useState('');
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

  // New Product Modal State
  const [showAddModal, setShowAddModal] = useState(false);
  const [newProdId, setNewProdId] = useState('');
  const [newProdName, setNewProdName] = useState('');

  // Crop Modal State
  const [showCropModal, setShowCropModal] = useState(false);
  const [upImg, setUpImg] = useState<string | ArrayBuffer | null>(null);
  const [crop, setCrop] = useState<CropType>();
  const [completedCrop, setCompletedCrop] = useState<PixelCrop>();
  const imgRef = useRef<HTMLImageElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const processFile = (file: File) => {
    setSelectedFile(file);
    const reader = new FileReader();
    reader.addEventListener('load', () => setUpImg(reader.result));
    reader.readAsDataURL(file);
    setShowCropModal(true);
  };

  const onSelectFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFile(e.target.files[0]);
    }
  };

  const onDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const onDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const onImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const { width, height } = e.currentTarget;
    const newCrop = centerAspectCrop(width, height);
    setCrop(newCrop);
    setCompletedCrop(convertToPixelCrop(newCrop, width, height));
  };

  const convertToPixelCrop = (crop: CropType, imageWidth: number, imageHeight: number): PixelCrop => {
    return {
      unit: 'px',
      x: crop.unit === '%' ? (crop.x / 100) * imageWidth : crop.x,
      y: crop.unit === '%' ? (crop.y / 100) * imageHeight : crop.y,
      width: crop.unit === '%' ? (crop.width / 100) * imageWidth : crop.width,
      height: crop.unit === '%' ? (crop.height / 100) * imageHeight : crop.height,
    };
  };

  const refreshProducts = async () => {
    try {
      const data = await prismApi.getProducts();
      setProducts(data);
    } catch (e) {
      console.error("Failed to fetch products", e);
    }
  };

  useEffect(() => {
    refreshProducts();
  }, []);

  const handleCreateProduct = async () => {
    if (!newProdId || !newProdName) return;
    await prismApi.addProduct({ id: newProdId, name: newProdName });
    setShowAddModal(false);
    setNewProdId('');
    setNewProdName('');
    refreshProducts();
  };

  const getCroppedImg = async (image: HTMLImageElement, crop: PixelCrop, fileName: string): Promise<Blob> => {
    const canvas = document.createElement('canvas');
    const scaleX = image.naturalWidth / image.width;
    const scaleY = image.naturalHeight / image.height;
    canvas.width = crop.width;
    canvas.height = crop.height;
    const ctx = canvas.getContext('2d');

    if (!ctx) {
      throw new Error('No 2d context');
    }

    ctx.drawImage(
      image,
      crop.x * scaleX,
      crop.y * scaleY,
      crop.width * scaleX,
      crop.height * scaleY,
      0,
      0,
      crop.width,
      crop.height
    );

    return new Promise((resolve, reject) => {
      canvas.toBlob((blob) => {
        if (!blob) {
          reject(new Error('Canvas is empty'));
          return;
        }
        resolve(blob);
      }, 'image/jpeg');
    });
  };

  const handleUploadRef = async () => {
    if (!selectedProduct || !completedCrop || !imgRef.current) return;

    try {
      const croppedBlob = await getCroppedImg(imgRef.current, completedCrop, 'new-ref.jpg');
      // Create a File from the Blob
      const file = new File([croppedBlob], 'reference.jpg', { type: 'image/jpeg' });

      await prismApi.uploadReference(selectedProduct.id, file);
      refreshProducts(); // Refresh to update count
      // Refresh current product details
      if (selectedProduct) {
        const updated = await prismApi.getProduct(selectedProduct.id);
        setSelectedProduct(updated);
      }
      refreshProducts();
      setShowCropModal(false);
      setUpImg(null);
      alert("Reference uploaded!");
    } catch (e) {
      console.error("Failed to create crop", e);
      alert("Failed to create crop");
    }
  };

  const handleSelectProduct = async (product: Product) => {
    setSelectedProduct(product); // Optimistic
    try {
      const fullData = await prismApi.getProduct(product.id);
      setSelectedProduct(fullData);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteReference = async (refId: string) => {
    if (!selectedProduct || !confirm('Are you sure you want to delete this reference?')) return;
    try {
      await prismApi.deleteReference(selectedProduct.id, refId);
      // Refresh details
      const updated = await prismApi.getProduct(selectedProduct.id);
      setSelectedProduct(updated);
      refreshProducts(); // Update counts
    } catch (e) {
      console.error("Failed to delete reference", e);
      alert("Failed to delete reference");
    }
  };

  const filteredProducts = products.filter(p =>
    p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="h-full flex flex-col gap-6 animate-in fade-in duration-500 relative">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Product Studio</h1>
          <p className="text-sm text-zinc-500">Universal SKU registry & vector reference library</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-5 py-2.5 rounded-xl transition-all font-bold text-sm shadow-[0_0_20px_rgba(37,99,235,0.4)]">
          <Plus size={18} />
          NEW REGISTRATION
        </button>
      </div>

      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-grow">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500" size={18} />
          <input
            type="text"
            placeholder="Search by ID, name, or metadata..."
            className="w-full bg-zinc-900 border border-zinc-800 rounded-xl pl-12 pr-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500/50"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        {/* Toggle View Buttons */}
        <div className="flex items-center border border-zinc-800 rounded-xl p-1 bg-zinc-900 shadow-inner">
          <button onClick={() => setViewMode('grid')} className={cn("p-2 rounded-lg transition-all", viewMode === 'grid' ? "bg-zinc-800 text-blue-500 shadow-lg" : "text-zinc-500 hover:text-zinc-300")}>
            <Grid2X2 size={18} />
          </button>
          <button onClick={() => setViewMode('list')} className={cn("p-2 rounded-lg transition-all", viewMode === 'list' ? "bg-zinc-800 text-blue-500 shadow-lg" : "text-zinc-500 hover:text-zinc-300")}>
            <List size={18} />
          </button>
        </div>
      </div>

      <div className="flex-grow overflow-auto pr-2 custom-scrollbar">
        {viewMode === 'grid' ? (
          <div className="columns-1 md:columns-2 lg:columns-3 xl:columns-4 gap-6 space-y-6">
            {filteredProducts.map(product => (
              <div
                key={product.id}
                onClick={() => handleSelectProduct(product)}
                className="break-inside-avoid glass-panel rounded-2xl overflow-hidden group hover:border-blue-500/50 transition-all duration-300 flex flex-col cursor-pointer hover:shadow-[0_10px_30px_rgba(0,0,0,0.5)] border border-zinc-800"
              >
                <div className="relative overflow-hidden bg-zinc-900 h-48 flex items-center justify-center">
                  {/* Placeholder image since backend doesn't return ref image URL in list */}
                  <ImageIcon className="text-zinc-800 w-16 h-16" />
                  <div className="absolute top-3 left-3 flex gap-2">
                    <span className="text-[9px] font-black text-white bg-blue-600 px-2 py-0.5 rounded uppercase tracking-widest">PRODUCT</span>
                  </div>
                </div>
                <div className="p-5">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-bold text-zinc-100 group-hover:text-blue-400 transition-colors tracking-tight">{product.name}</h3>
                    <span className="text-[10px] mono text-zinc-600 font-bold">{product.id}</span>
                  </div>
                  <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-widest text-zinc-500 mt-4 pt-4 border-t border-zinc-800/50">
                    <div className="flex items-center gap-1.5">
                      <History size={12} className="text-zinc-600" />
                      <span>{product.reference_count} REFS</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="glass-panel rounded-2xl overflow-hidden border border-zinc-800">
            <table className="w-full text-sm">
              <thead className="bg-zinc-900/50 text-zinc-500 border-b border-zinc-800">
                <tr>
                  <th className="text-left py-4 px-6 font-black uppercase tracking-widest text-[10px]">Product Identity</th>
                  <th className="text-left py-4 px-6 font-black uppercase tracking-widest text-[10px]">Created</th>
                  <th className="text-left py-4 px-6 font-black uppercase tracking-widest text-[10px]">References</th>
                </tr>
              </thead>
              <tbody>
                {filteredProducts.map(product => (
                  <tr key={product.id} onClick={() => handleSelectProduct(product)} className="border-b border-zinc-800/50 hover:bg-zinc-800/20 transition-colors cursor-pointer group">
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-lg border border-zinc-800 bg-zinc-900 flex items-center justify-center">
                          <PackageCheck size={20} className="text-zinc-600" />
                        </div>
                        <div>
                          <div className="font-bold text-zinc-100 group-hover:text-blue-400 transition-colors">{product.name}</div>
                          <div className="text-[10px] text-zinc-600 mono font-bold">{product.id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="py-4 px-6 text-zinc-400 mono text-xs">{product.created_at || 'N/A'}</td>
                    <td className="py-4 px-6">
                      <span className="mono font-bold text-blue-500">{product.reference_count}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add Product Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
          <div className="bg-zinc-900 border border-zinc-800 p-8 rounded-2xl w-full max-w-md space-y-4">
            <h2 className="text-xl font-bold">Register New Product</h2>
            <input className="w-full bg-black border border-zinc-800 p-3 rounded-lg" placeholder="Product ID (e.g. coke-can)" value={newProdId} onChange={e => setNewProdId(e.target.value)} />
            <input className="w-full bg-black border border-zinc-800 p-3 rounded-lg" placeholder="Product Name (e.g. Coke Can)" value={newProdName} onChange={e => setNewProdName(e.target.value)} />
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowAddModal(false)} className="px-4 py-2 text-zinc-400 hover:text-white">Cancel</button>
              <button onClick={handleCreateProduct} className="px-4 py-2 bg-blue-600 text-white rounded-lg font-bold">Create</button>
            </div>
          </div>
        </div>
      )}

      {/* Crop Modal */}
      {showCropModal && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="w-fit min-w-[600px] max-w-6xl bg-zinc-950 border border-zinc-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
            <div className="flex justify-between items-center p-6 border-b border-zinc-800 bg-zinc-900/50">
              <div>
                <h2 className="text-xl font-bold">Crop Reference Image</h2>
                <p className="text-sm text-zinc-500">Select the area containing ONLY the product.</p>
              </div>
              <button onClick={() => { setShowCropModal(false); setUpImg(null); }} className="p-2 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors">
                <X size={20} />
              </button>
            </div>

            <div className="flex-1 overflow-auto p-8 flex items-center justify-center bg-black/40">
              <div className="relative shadow-2xl border border-zinc-800/50">
                <ReactCrop
                  crop={crop}
                  onChange={(c) => setCrop(c)}
                  onComplete={(c) => setCompletedCrop(c)}
                  aspect={undefined}
                >
                  <img
                    ref={imgRef}
                    src={upImg as string}
                    alt="Upload"
                    className="max-h-[65vh] object-contain block"
                    onLoad={onImageLoad}
                  />
                </ReactCrop>
              </div>
            </div>

            <div className="p-6 border-t border-zinc-800 flex justify-end gap-3 bg-zinc-900/50">
              <button onClick={() => { setShowCropModal(false); setUpImg(null); }} className="px-5 py-2.5 font-bold text-sm text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors">
                CANCEL
              </button>
              <button
                onClick={handleUploadRef}
                disabled={!completedCrop?.width || !completedCrop?.height}
                className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-bold text-sm shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-all"
              >
                <Check size={16} />
                CONFIRM CROP & UPLOAD
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Side Drawer Detail View */}
      {selectedProduct && (
        <div className="fixed inset-0 z-50 flex justify-end animate-in fade-in duration-300">
          <div className="absolute inset-0 bg-zinc-950/60 backdrop-blur-sm" onClick={() => setSelectedProduct(null)} />
          <div className="relative w-full max-w-lg h-full bg-[#09090b] border-l border-zinc-800 shadow-2xl animate-in slide-in-from-right duration-500 p-8 overflow-y-auto flex flex-col gap-8">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-600/10 border border-blue-500/20 rounded-xl flex items-center justify-center text-blue-500">
                  <ShieldCheck size={24} />
                </div>
                <div>
                  <h2 className="text-xl font-bold tracking-tight">{selectedProduct.name}</h2>
                  <p className="text-[10px] font-bold mono text-zinc-500 uppercase tracking-widest">Registry ID: {selectedProduct.id}</p>
                </div>
              </div>
              <button onClick={() => setSelectedProduct(null)} className="p-2 text-zinc-500 hover:text-zinc-100 bg-zinc-900 border border-zinc-800 rounded-lg">
                <X size={20} />
              </button>
            </div>

            <div className="space-y-6">
              <div className="glass-panel p-6 rounded-2xl border border-zinc-800 space-y-4">
                <h3 className="text-xs font-black uppercase tracking-widest text-zinc-500">Asset Profile</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-zinc-900/50 p-3 rounded-xl border border-zinc-800">
                    <span className="text-[9px] font-bold text-zinc-600 uppercase block mb-1">Total References</span>
                    <span className="text-xl font-black mono text-blue-400">{selectedProduct.reference_count}</span>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-black uppercase tracking-widest text-zinc-500">Reference Library</h3>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  {selectedProduct.reference_images?.map((ref) => (
                    <div key={ref.id} className="aspect-square rounded-xl overflow-hidden border border-zinc-800 relative group bg-zinc-900">
                      <img
                        src={`${API_URL}/${ref.url}`}
                        alt={ref.id}
                        className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity"
                        onError={(e) => {
                          (e.target as HTMLImageElement).src = 'https://placehold.co/400?text=Error';
                        }}
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-end p-2">
                        <span className="text-[9px] text-white mono truncate">{ref.id}</span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteReference(ref.id);
                          }}
                          className="mt-1 p-1 bg-red-600/80 hover:bg-red-500 text-white rounded-md self-end"
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                    </div>
                  ))}
                  <div
                    className={cn(
                      "aspect-square rounded-xl border-2 border-dashed flex flex-col items-center justify-center gap-2 transition-all cursor-pointer relative",
                      isDragging
                        ? "border-blue-500 bg-blue-500/10 text-blue-400"
                        : "border-zinc-800 text-zinc-600 hover:border-zinc-700 hover:text-zinc-500"
                    )}
                    onDragOver={onDragOver}
                    onDragLeave={onDragLeave}
                    onDrop={onDrop}
                  >
                    <input type="file" className="absolute inset-0 opacity-0 cursor-pointer" onChange={onSelectFile} accept="image/*" />
                    <ImageIcon size={24} />
                    <span className="text-[9px] font-bold uppercase tracking-widest text-center">{isDragging ? "Drop to Upload" : "Drop New Matrix"}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
