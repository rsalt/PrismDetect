
import React, { useState } from 'react';
import { View } from './types';
import { Layout } from './components/Layout';
import { Dashboard } from './components/Dashboard';
import { ProductStudio } from './components/ProductStudio';
import { VisionLab } from './components/VisionLab';
import { BatchForensics } from './components/BatchForensics';

const SettingsPlaceholder = () => (
  <div className="flex flex-col items-center justify-center h-full text-zinc-500 space-y-6 animate-in fade-in zoom-in duration-500">
    <div className="w-24 h-24 bg-zinc-900 rounded-[2rem] flex items-center justify-center border border-zinc-800 shadow-2xl">
      <span className="text-4xl">⚙️</span>
    </div>
    <div className="text-center">
       <h2 className="text-2xl font-black italic tracking-tighter text-zinc-100 uppercase">Engine Configuration</h2>
       <p className="max-w-xs text-sm mt-2 text-zinc-500 uppercase font-bold tracking-widest">Global routing, API handshakes, and Webhook orchestration</p>
    </div>
    <div className="grid grid-cols-2 gap-4 w-full max-w-md">
       <div className="p-4 bg-zinc-900/50 border border-zinc-800 rounded-2xl text-center">
          <p className="text-[9px] font-black text-zinc-600 uppercase mb-1">Active Model</p>
          <p className="text-xs font-bold text-blue-500 mono">Gemini-3-Flash-RT</p>
       </div>
       <div className="p-4 bg-zinc-900/50 border border-zinc-800 rounded-2xl text-center">
          <p className="text-[9px] font-black text-zinc-600 uppercase mb-1">API Status</p>
          <p className="text-xs font-bold text-emerald-500 mono">Verified (v2.4.1)</p>
       </div>
    </div>
  </div>
);

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>(View.DASHBOARD);

  const renderView = () => {
    switch (currentView) {
      case View.DASHBOARD:
        return <Dashboard />;
      case View.PRODUCT_STUDIO:
        return <ProductStudio />;
      case View.VISION_LAB:
        return <VisionLab />;
      case View.BATCH_FORENSICS:
        return <BatchForensics />;
      case View.SETTINGS:
        return <SettingsPlaceholder />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <Layout currentView={currentView} onViewChange={setCurrentView}>
      {renderView()}
    </Layout>
  );
};

export default App;
