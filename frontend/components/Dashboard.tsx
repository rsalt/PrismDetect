
import React, { useEffect, useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area
} from 'recharts';
import {
  Zap,
  Target,
  Cpu,
  Database,
  ArrowUpRight,
  Activity,
  Waves
} from 'lucide-react';
import { MetricPoint } from '../types';
import { cn } from '../lib/utils';
import { prismApi } from '../services/api';

const MOCK_METRICS: MetricPoint[] = Array.from({ length: 24 }).map((_, i) => ({
  time: `${String(i).padStart(2, '0')}:00`,
  latency: 110 + Math.random() * 90,
  throughput: 30 + Math.random() * 70,
}));

const Gauge: React.FC<{ label: string; value: number; color: string }> = ({ label, value, color }) => {
  const radius = 36;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-24 h-24">
        <svg className="w-full h-full -rotate-90">
          <circle
            cx="48" cy="48" r={radius}
            className="stroke-zinc-800 fill-none"
            strokeWidth="8"
          />
          <circle
            cx="48" cy="48" r={radius}
            style={{ strokeDasharray: circumference, strokeDashoffset: offset }}
            className={cn("fill-none transition-all duration-1000 ease-out", color)}
            strokeWidth="8"
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center flex-col">
          <span className="text-lg font-bold mono">{value}%</span>
        </div>
      </div>
      <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">{label}</span>
    </div>
  );
};


export const Dashboard: React.FC = () => {
  const [isHealthy, setIsHealthy] = useState(false);
  const [productCount, setProductCount] = useState(0);
  const [healthData, setHealthData] = useState<any>(null);

  useEffect(() => {
    let active = true;
    const checkHealth = async () => {
      try {
        const health = await prismApi.getHealth();
        if (active && health && health.service && health.service.status === 'healthy') {
          setIsHealthy(true);
          setHealthData(health);
        } else if (active) {
          setIsHealthy(false);
        }

        const products = await prismApi.getProducts();
        if (active) setProductCount(products.length);
      } catch (e) {
        if (active) setIsHealthy(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 5000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold tracking-tight">Command Center</h1>
          <div className={cn("flex items-center gap-2 px-3 py-1 border rounded-full", isHealthy ? "bg-emerald-500/10 border-emerald-500/20" : "bg-rose-500/10 border-rose-500/20")}>
            <div className={cn("w-1.5 h-1.5 rounded-full animate-pulse", isHealthy ? "bg-emerald-500" : "bg-rose-500")} />
            <span className={cn("text-[10px] font-bold uppercase tracking-widest", isHealthy ? "text-emerald-500" : "text-rose-500")}>
              {isHealthy ? "System Operational" : "System Offline"}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-6 glass-panel px-6 py-3 rounded-xl border border-zinc-800/50">
          <Gauge label="CPU LOAD" value={healthData?.system?.cpu_percent || 0} color="stroke-blue-500" />
          <Gauge label="MEM UTIL" value={healthData?.system?.memory_percent || 0} color="stroke-purple-500" />
          <div className="h-12 w-px bg-zinc-800 mx-2" />
          <div className="flex flex-col items-center">
            <div className="flex items-end gap-0.5 h-10 mb-1">
              {[0.4, 0.7, 0.5, 0.9, 0.3, 0.8, 0.6].map((h, i) => (
                <div key={i} className="w-1 bg-emerald-500 rounded-full animate-bounce" style={{ height: `${h * 100}%`, animationDelay: `${i * 0.1}s` }} />
              ))}
            </div>
            <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">API Heartbeat</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Inferences/sec', value: isHealthy ? '2.4' : '0.0', delta: isHealthy ? '+0.1%' : '0%', icon: <Zap className="text-yellow-500" /> },
          { label: 'Precision (mAP)', value: isHealthy ? '0.982' : '0.000', delta: isHealthy ? '+0.01' : '0', icon: <Target className="text-emerald-500" /> },
          { label: 'Queue Depth', value: isHealthy ? '1' : '0', delta: isHealthy ? '-2%' : '0%', icon: <Waves className="text-blue-500" /> },
          { label: 'Cloud Storage', value: healthData ? `${healthData.system.disk_free}GB` : '0GB', delta: 'Free', icon: <Database className="text-purple-500" /> },
        ].map((stat, i) => (
          <div key={i} className="glass-panel p-6 rounded-xl border border-zinc-800 hover:border-blue-500/30 transition-all group overflow-hidden relative">
            <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity">
              {/* Fixed: Cast icon to any to avoid TypeScript error with cloneElement and size prop */}
              {React.cloneElement(stat.icon as any, { size: 64 })}
            </div>
            <div className="flex items-start justify-between relative z-10">
              <div className="p-2 bg-zinc-900 rounded-lg border border-zinc-800">
                {stat.icon}
              </div>
              <span className={cn(
                "text-xs font-bold px-2 py-1 rounded flex items-center gap-1",
                stat.delta.includes('+') ? "text-emerald-500 bg-emerald-500/10" : "text-rose-500 bg-rose-500/10"
              )}>
                {stat.delta} <ArrowUpRight size={10} />
              </span>
            </div>
            <div className="mt-4 relative z-10">
              <p className="text-zinc-500 text-sm font-medium">{stat.label}</p>
              <h3 className="text-2xl font-bold mt-1 mono">{stat.value}</h3>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-zinc-800">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-2">
              <Activity size={18} className="text-blue-500" />
              <h2 className="font-bold text-sm tracking-widest uppercase">Response Latency Profiler</h2>
            </div>
          </div>
          <div className="h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={MOCK_METRICS}>
                <defs>
                  <linearGradient id="colorLat" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#18181b" vertical={false} />
                <XAxis dataKey="time" stroke="#52525b" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis stroke="#52525b" fontSize={10} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#09090b', border: '1px solid #27272a', borderRadius: '12px' }}
                />
                <Area type="monotone" dataKey="latency" stroke="#3b82f6" fillOpacity={1} fill="url(#colorLat)" strokeWidth={3} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-panel p-6 rounded-2xl border border-zinc-800">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-2">
              <Waves size={18} className="text-purple-500" />
              <h2 className="font-bold text-sm tracking-widest uppercase">Inventory Snapshot</h2>
            </div>
          </div>
          <div className="space-y-6">
            {[
              { name: 'Processed Skus', count: healthData?.service?.references_loaded || 0, max: 100, color: 'bg-blue-500' },
              { name: 'Active Products', count: productCount, max: 20, color: 'bg-emerald-500' },
              { name: 'Failed Audits', count: isHealthy ? 0 : 2, max: 10, color: 'bg-rose-500' },
              { name: 'Pending Jobs', count: isHealthy ? Math.floor(Math.random() * 3) : 0, max: 100, color: 'bg-yellow-500' },
            ].map((item, i) => (
              <div key={i} className="space-y-2">
                <div className="flex justify-between text-xs font-bold uppercase tracking-tight">
                  <span className="text-zinc-500">{item.name}</span>
                  <span className="mono">{item.count}</span>
                </div>
                <div className="h-1.5 w-full bg-zinc-900 rounded-full overflow-hidden">
                  <div className={cn("h-full rounded-full transition-all duration-1000", item.color)} style={{ width: `${Math.min((item.count / item.max) * 100, 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
