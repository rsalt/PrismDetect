
import React, { useState } from 'react';
import { 
  History, Upload, Search, Download, Filter, 
  Loader2, CheckCircle2, AlertTriangle, 
  SortDesc, SortAsc, FileText, ArrowDown, ArrowUp
} from 'lucide-react';
import { BatchItem } from '../types';
import { cn } from '../lib/utils';

const MOCK_BATCH: BatchItem[] = [
  { id: 'JOB-401', name: 'scan_312.jpg', thumbnail: 'https://picsum.photos/80/80?a=1', topDetection: 'Coke 330ml', confidence: 0.98, latency: 142, status: 'completed' },
  { id: 'JOB-402', name: 'img_test_2.png', thumbnail: 'https://picsum.photos/80/80?a=2', topDetection: 'Pepsi Blue', confidence: 0.42, latency: 210, status: 'completed' },
  { id: 'JOB-403', name: 'frame_881.webp', thumbnail: 'https://picsum.photos/80/80?a=3', topDetection: 'Monster Ultra', confidence: 0.88, latency: 156, status: 'completed' },
  { id: 'JOB-404', name: 'asset_90.jpg', thumbnail: 'https://picsum.photos/80/80?a=4', topDetection: 'Unknown (Low Conf)', confidence: 0.12, latency: 305, status: 'failed' },
  { id: 'JOB-405', name: 'capture_4.jpg', thumbnail: 'https://picsum.photos/80/80?a=5', topDetection: 'Red Bull 250', confidence: 0.99, latency: 130, status: 'completed' },
  { id: 'JOB-406', name: 'scan_99.png', thumbnail: 'https://picsum.photos/80/80?a=6', topDetection: 'Sprite 500ml', confidence: 0.76, latency: 168, status: 'completed' },
];

export const BatchForensics: React.FC = () => {
  const [items, setItems] = useState<BatchItem[]>(MOCK_BATCH);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [sortConfig, setSortConfig] = useState<{ key: keyof BatchItem, direction: 'asc' | 'desc' }>({ key: 'confidence', direction: 'asc' });

  const startBatch = () => {
    setIsProcessing(true);
    setProgress(0);
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsProcessing(false);
          return 100;
        }
        return prev + 5;
      });
    }, 200);
  };

  const sortedItems = [...items].sort((a, b) => {
    const valA = a[sortConfig.key];
    const valB = b[sortConfig.key];
    if (typeof valA === 'number' && typeof valB === 'number') {
      return sortConfig.direction === 'asc' ? valA - valB : valB - valA;
    }
    return 0;
  });

  const toggleSort = (key: keyof BatchItem) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  return (
    <div className="h-full flex flex-col gap-6 animate-in slide-in-from-right-4 duration-700">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Batch Forensics</h1>
          <p className="text-sm text-zinc-500">Audit bulk inference results & detect edge case failures</p>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-zinc-100 px-4 py-2 rounded-xl transition-all font-bold text-sm">
             <Download size={18} />
             EXPORT CSV
          </button>
          <button 
            onClick={startBatch}
            disabled={isProcessing}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white px-5 py-2.5 rounded-xl transition-all font-bold text-sm shadow-[0_0_20px_rgba(37,99,235,0.4)]"
          >
            {isProcessing ? <Loader2 size={18} className="animate-spin" /> : <Upload size={18} />}
            INITIATE BULK QUEUE
          </button>
        </div>
      </div>

      {isProcessing && (
        <div className="glass-panel p-6 rounded-2xl border border-blue-500/20 bg-blue-600/5 animate-in fade-in zoom-in duration-300">
           <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                 <Loader2 className="animate-spin text-blue-500" />
                 <span className="text-sm font-bold uppercase tracking-widest text-blue-400">Processing Node Cluster Alpha-4</span>
              </div>
              <span className="text-sm font-black mono text-blue-500">{progress}%</span>
           </div>
           <div className="h-2 w-full bg-zinc-900 rounded-full overflow-hidden border border-zinc-800">
              <div className="h-full bg-blue-600 transition-all duration-300 ease-out shadow-[0_0_10px_rgba(37,99,235,0.8)]" style={{ width: `${progress}%` }} />
           </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
         <div className="lg:col-span-3 glass-panel rounded-2xl border border-zinc-800 overflow-hidden flex flex-col shadow-2xl">
            <div className="px-6 py-4 border-b border-zinc-800 flex items-center justify-between bg-zinc-900/30">
               <div className="flex items-center gap-4">
                  <h3 className="text-xs font-black uppercase tracking-widest text-zinc-500">Inference Audit Log</h3>
                  <div className="relative">
                     <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-600" />
                     <input type="text" placeholder="Search logs..." className="bg-zinc-950 border border-zinc-800 rounded-lg pl-9 pr-3 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500/50 w-48" />
                  </div>
               </div>
               <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold text-zinc-600 uppercase">Sort Profile:</span>
                  <button onClick={() => toggleSort('confidence')} className={cn("px-2 py-1 rounded text-[10px] font-bold border transition-all flex items-center gap-1", sortConfig.key === 'confidence' ? "bg-blue-600/10 border-blue-500 text-blue-400" : "bg-zinc-900 border-zinc-800 text-zinc-500")}>
                     {sortConfig.key === 'confidence' && (sortConfig.direction === 'asc' ? <ArrowUp size={12}/> : <ArrowDown size={12}/>)}
                     CONFIDENCE
                  </button>
               </div>
            </div>
            <div className="overflow-auto max-h-[600px] custom-scrollbar">
               <table className="w-full text-xs">
                  <thead className="bg-zinc-950/50 sticky top-0 z-10 text-zinc-500 border-b border-zinc-800">
                     <tr>
                        <th className="py-3 px-6 text-left font-bold uppercase tracking-widest text-[9px]">Thumbnail</th>
                        <th className="py-3 px-6 text-left font-bold uppercase tracking-widest text-[9px]">Asset Node</th>
                        <th className="py-3 px-6 text-left font-bold uppercase tracking-widest text-[9px]">Top Detection</th>
                        <th className="py-3 px-6 text-right font-bold uppercase tracking-widest text-[9px] cursor-pointer" onClick={() => toggleSort('confidence')}>
                           <div className="flex items-center justify-end gap-1">Confidence {sortConfig.key === 'confidence' ? (sortConfig.direction === 'asc' ? <SortAsc size={12}/> : <SortDesc size={12}/>) : null}</div>
                        </th>
                        <th className="py-3 px-6 text-right font-bold uppercase tracking-widest text-[9px]">Latency</th>
                        <th className="py-3 px-6 text-center font-bold uppercase tracking-widest text-[9px]">Health</th>
                     </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/50">
                     {sortedItems.map(item => (
                        <tr key={item.id} className="hover:bg-zinc-800/30 transition-colors group">
                           <td className="py-3 px-6">
                              <img src={item.thumbnail} className="w-10 h-10 rounded-lg border border-zinc-800 object-cover" />
                           </td>
                           <td className="py-3 px-6 font-bold mono text-zinc-400 group-hover:text-blue-400 transition-colors">
                              {item.id}
                              <div className="text-[9px] text-zinc-600 font-normal">{item.name}</div>
                           </td>
                           <td className="py-3 px-6 font-bold text-zinc-200 uppercase tracking-tight italic">{item.topDetection}</td>
                           <td className="py-3 px-6 text-right">
                              <span className={cn(
                                 "mono font-bold text-sm",
                                 item.confidence > 0.8 ? "text-emerald-500" : item.confidence > 0.4 ? "text-yellow-500" : "text-rose-500"
                              )}>
                                 {(item.confidence * 100).toFixed(1)}%
                              </span>
                           </td>
                           <td className="py-3 px-6 text-right mono text-zinc-500">{item.latency}ms</td>
                           <td className="py-3 px-6 text-center">
                              {item.status === 'completed' ? (
                                 <CheckCircle2 size={16} className="text-emerald-500 mx-auto" />
                              ) : (
                                 <AlertTriangle size={16} className="text-rose-500 mx-auto animate-pulse" />
                              )}
                           </td>
                        </tr>
                     ))}
                  </tbody>
               </table>
            </div>
         </div>

         <div className="space-y-6">
            <div className="glass-panel p-6 rounded-2xl border border-zinc-800">
               <h3 className="text-xs font-black uppercase tracking-widest text-zinc-500 mb-6 flex items-center gap-2">
                  <FileText size={14} className="text-blue-500" />
                  Forensic Summary
               </h3>
               <div className="space-y-4">
                  {[
                    { label: 'Mean Precision', val: '0.882', color: 'text-emerald-500' },
                    { label: 'Low-Conf Anomalies', val: '2 Detected', color: 'text-rose-500' },
                    { label: 'Avg Latency', val: '158ms', color: 'text-blue-500' },
                    { label: 'Cloud Egress', val: '24.2MB', color: 'text-zinc-400' },
                  ].map((stat, i) => (
                    <div key={i} className="flex items-center justify-between border-b border-zinc-800/50 pb-3">
                       <span className="text-[10px] font-bold text-zinc-500 uppercase">{stat.label}</span>
                       <span className={cn("text-xs font-black mono", stat.color)}>{stat.val}</span>
                    </div>
                  ))}
               </div>
            </div>

            <div className="glass-panel p-6 rounded-2xl border border-zinc-800 bg-zinc-900/20">
               <h3 className="text-[10px] font-black uppercase tracking-widest text-zinc-600 mb-4">Forensic Tips</h3>
               <p className="text-[10px] leading-relaxed text-zinc-500 italic">
                  "Identify edge cases where the confidence falls below 0.3. These assets usually require more reference embeddings or better lighting profiles in the Product Studio."
               </p>
            </div>
         </div>
      </div>
    </div>
  );
};
