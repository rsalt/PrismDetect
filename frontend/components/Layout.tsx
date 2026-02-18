
import React from 'react';
import { 
  LayoutDashboard, 
  Package, 
  ScanSearch, 
  History, 
  Settings, 
  Activity,
  ChevronRight,
  User,
  LogOut
} from 'lucide-react';
import { View } from '../types';
import { cn } from '../lib/utils';

interface SidebarItemProps {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onClick: () => void;
}

const SidebarItem: React.FC<SidebarItemProps> = ({ icon, label, active, onClick }) => (
  <button
    onClick={onClick}
    className={cn(
      "w-full flex items-center gap-3 px-4 py-3 text-sm font-medium transition-all rounded-lg group",
      active 
        ? "bg-blue-600/10 text-blue-400 border border-blue-600/20 shadow-[0_0_15px_rgba(37,99,235,0.1)]" 
        : "text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/50"
    )}
  >
    <span className={cn("transition-transform group-hover:scale-110", active && "text-blue-500")}>
      {icon}
    </span>
    <span className="flex-grow text-left">{label}</span>
    {active && <div className="w-1 h-4 bg-blue-500 rounded-full" />}
  </button>
);

interface LayoutProps {
  currentView: View;
  onViewChange: (view: View) => void;
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ currentView, onViewChange, children }) => {
  return (
    <div className="flex h-screen w-full bg-[#09090b] text-zinc-100 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 border-r border-zinc-800 bg-zinc-950/50 flex flex-col p-4 z-20">
        <div className="flex items-center gap-3 px-2 mb-8 mt-2">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shadow-[0_0_20px_rgba(37,99,235,0.4)]">
            <ScanSearch size={20} className="text-white" />
          </div>
          <span className="font-bold text-lg tracking-tight">PrismDetect <span className="text-blue-500">Ops</span></span>
        </div>

        <nav className="flex-grow space-y-2">
          <SidebarItem 
            icon={<LayoutDashboard size={18} />} 
            label="Command Center" 
            active={currentView === View.DASHBOARD}
            onClick={() => onViewChange(View.DASHBOARD)}
          />
          <SidebarItem 
            icon={<Package size={18} />} 
            label="Product Studio" 
            active={currentView === View.PRODUCT_STUDIO}
            onClick={() => onViewChange(View.PRODUCT_STUDIO)}
          />
          <SidebarItem 
            icon={<ScanSearch size={18} />} 
            label="Vision Lab" 
            active={currentView === View.VISION_LAB}
            onClick={() => onViewChange(View.VISION_LAB)}
          />
          <SidebarItem 
            icon={<History size={18} />} 
            label="Batch Forensics" 
            active={currentView === View.BATCH_FORENSICS}
            onClick={() => onViewChange(View.BATCH_FORENSICS)}
          />
        </nav>

        <div className="pt-4 border-t border-zinc-800 space-y-2">
           <SidebarItem 
            icon={<Settings size={18} />} 
            label="Settings" 
            active={currentView === View.SETTINGS}
            onClick={() => onViewChange(View.SETTINGS)}
          />
          <div className="px-4 py-4 flex items-center gap-3">
             <div className="w-10 h-10 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center">
                <User size={20} className="text-zinc-400" />
             </div>
             <div className="flex flex-col overflow-hidden">
                <span className="text-sm font-medium truncate">Engineer Admin</span>
                <span className="text-xs text-zinc-500 truncate italic">Prism Node #402</span>
             </div>
          </div>
          <div className="flex items-center justify-between px-2 pt-2">
             <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-[10px] uppercase font-bold text-zinc-500 tracking-widest">System Online</span>
             </div>
             <button className="text-zinc-500 hover:text-zinc-300 transition-colors">
                <LogOut size={14} />
             </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-grow flex flex-col min-w-0 h-full relative">
        {/* Header */}
        <header className="h-16 border-b border-zinc-800 px-8 flex items-center justify-between bg-zinc-950/20 backdrop-blur-md z-10">
          <div className="flex items-center gap-4 text-sm">
            <span className="text-zinc-500">Home</span>
            <ChevronRight size={14} className="text-zinc-600" />
            <span className="font-medium capitalize">{currentView.replace('_', ' ').toLowerCase()}</span>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-zinc-900 border border-zinc-800 rounded-md">
              <Activity size={14} className="text-blue-500" />
              <span className="text-xs font-medium mono">Lat: 142ms</span>
            </div>
          </div>
        </header>

        {/* View Container */}
        <div className="flex-grow overflow-auto p-8 bg-[#09090b]">
           {children}
        </div>
      </main>
    </div>
  );
};
