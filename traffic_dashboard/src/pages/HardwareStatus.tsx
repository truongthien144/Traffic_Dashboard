import React, { useState } from 'react';
import { 
  Cpu, HardDrive, Thermometer, Zap, Server, Activity, 
  Database, RefreshCw, AlertCircle, CheckCircle2, Clock, ArrowRightLeft
} from 'lucide-react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';

// Mock Data cho biểu đồ nhiệt độ Raspberry Pi
const cpuTempData = [
  { time: '10:00', temp: 55 }, { time: '10:05', temp: 58 }, { time: '10:10', temp: 62 },
  { time: '10:15', temp: 65 }, { time: '10:20', temp: 63 }, { time: '10:25', temp: 60 },
  { time: '10:30', temp: 61 }, { time: '10:35', temp: 59 },
];

const HardwareStatus: React.FC = () => {
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => setIsRefreshing(false), 1000);
  };

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 ease-out max-w-7xl mx-auto">
      
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-extrabold text-blue-950 tracking-tight mb-1">Trạng thái Phần cứng</h1>
          <p className="text-slate-500 font-medium">Giám sát sức khỏe Edge Node và thiết bị vi điều khiển.</p>
        </div>
        <button 
          onClick={handleRefresh}
          className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 text-slate-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all shadow-sm font-semibold text-sm cursor-pointer active:scale-95"
        >
          <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-blue-600' : ''}`} />
          Đồng bộ Dữ liệu
        </button>
      </div>

      {/* SECTION 1: EDGE NODE (RASPBERRY PI) METRICS */}
      <h2 className="text-lg font-bold text-blue-950 mb-4 flex items-center gap-2">
        <Server className="w-5 h-5 text-indigo-600" /> Trung tâm Xử lý Biên (Edge Node)
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        
        {/* CPU Usage */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm cursor-default hover:border-blue-200 transition-colors">
          <div className="flex justify-between items-start mb-4">
            <div className="w-10 h-10 bg-blue-50 text-blue-600 rounded-lg flex items-center justify-center">
              <Cpu className="w-5 h-5" />
            </div>
            <span className="text-xs font-bold text-amber-600 bg-amber-50 px-2 py-1 rounded-md border border-amber-100">Medium Load</span>
          </div>
          <p className="text-xs font-bold text-slate-500 mb-1 uppercase tracking-wider">CPU Usage</p>
          <div className="flex items-baseline gap-2 mb-3">
            <h3 className="text-3xl font-black text-blue-950">68<span className="text-lg text-slate-400 font-bold">%</span></h3>
          </div>
          <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
            <div className="bg-amber-500 h-full w-[68%] rounded-full"></div>
          </div>
        </div>

        {/* RAM Usage */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm cursor-default hover:border-blue-200 transition-colors">
          <div className="flex justify-between items-start mb-4">
            <div className="w-10 h-10 bg-indigo-50 text-indigo-600 rounded-lg flex items-center justify-center">
              <Database className="w-5 h-5" />
            </div>
            <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded-md border border-emerald-100">Safe</span>
          </div>
          <p className="text-xs font-bold text-slate-500 mb-1 uppercase tracking-wider">RAM Memory</p>
          <div className="flex items-baseline gap-2 mb-3">
            <h3 className="text-3xl font-black text-blue-950">2.4<span className="text-lg text-slate-400 font-bold">/4 GB</span></h3>
          </div>
          <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
            <div className="bg-indigo-500 h-full w-[60%] rounded-full"></div>
          </div>
        </div>

        {/* Temperature */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm cursor-default hover:border-blue-200 transition-colors">
          <div className="flex justify-between items-start mb-4">
            <div className="w-10 h-10 bg-red-50 text-red-600 rounded-lg flex items-center justify-center">
              <Thermometer className="w-5 h-5" />
            </div>
            <span className="text-xs font-bold text-red-600 bg-red-50 px-2 py-1 rounded-md border border-red-100 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" /> Cảnh báo
            </span>
          </div>
          <p className="text-xs font-bold text-slate-500 mb-1 uppercase tracking-wider">Core Temp</p>
          <div className="flex items-baseline gap-2 mb-3">
            <h3 className="text-3xl font-black text-red-600">65<span className="text-lg text-red-400 font-bold">°C</span></h3>
          </div>
          <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
            <div className="bg-red-500 h-full w-[85%] rounded-full animate-pulse"></div>
          </div>
        </div>

        {/* Storage / SD Card */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm cursor-default hover:border-blue-200 transition-colors">
          <div className="flex justify-between items-start mb-4">
            <div className="w-10 h-10 bg-emerald-50 text-emerald-600 rounded-lg flex items-center justify-center">
              <HardDrive className="w-5 h-5" />
            </div>
            <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded-md border border-emerald-100">Healthy</span>
          </div>
          <p className="text-xs font-bold text-slate-500 mb-1 uppercase tracking-wider">Storage (SD Card)</p>
          <div className="flex items-baseline gap-2 mb-3">
            <h3 className="text-3xl font-black text-blue-950">45<span className="text-lg text-slate-400 font-bold">%</span></h3>
          </div>
          <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
            <div className="bg-emerald-500 h-full w-[45%] rounded-full"></div>
          </div>
        </div>
      </div>

      {/* SECTION 2: MCU (ESP32) - Đã làm gọn lại */}
      <h2 className="text-lg font-bold text-blue-950 mb-4 flex items-center gap-2 mt-10">
        <Zap className="w-5 h-5 text-amber-500" /> Vi điều khiển ESP32
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        
        {/* Kết nối Serial/MQTT */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-center cursor-default">
          <div className="flex items-center justify-between mb-4">
            <div className="w-10 h-10 bg-emerald-50 text-emerald-600 rounded-lg flex items-center justify-center shadow-sm">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-100">Online</span>
          </div>
          <p className="text-xs font-bold text-slate-500 mb-1 uppercase tracking-wider">Trạng thái Giao tiếp</p>
          <h3 className="text-2xl font-black text-blue-950 mb-1">Ổn định</h3>
          <p className="text-sm font-medium text-slate-400">Độ trễ phản hồi: 12ms</p>
        </div>

        {/* Uptime */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-center cursor-default">
          <div className="flex items-center justify-between mb-4">
            <div className="w-10 h-10 bg-blue-50 text-blue-600 rounded-lg flex items-center justify-center shadow-sm">
              <Clock className="w-5 h-5" />
            </div>
          </div>
          <p className="text-xs font-bold text-slate-500 mb-1 uppercase tracking-wider">Thời gian Hoạt động</p>
          <h3 className="text-2xl font-black text-blue-950 mb-1">02:45:10</h3>
          <p className="text-sm font-medium text-slate-400">Giờ : Phút : Giây</p>
        </div>

        {/* Packet Gửi/Nhận */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-center cursor-default">
          <div className="flex items-center justify-between mb-4">
            <div className="w-10 h-10 bg-indigo-50 text-indigo-600 rounded-lg flex items-center justify-center shadow-sm">
              <ArrowRightLeft className="w-5 h-5" />
            </div>
          </div>
          <p className="text-xs font-bold text-slate-500 mb-1 uppercase tracking-wider">Lưu lượng Dữ liệu</p>
          <h3 className="text-2xl font-black text-blue-950 mb-1">1,245 / 1,240</h3>
          <p className="text-sm font-medium text-slate-400">Packets (Tx / Rx)</p>
        </div>
      </div>

      {/* SECTION 3: SYSTEM CHARTS */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm cursor-default">
        <h3 className="font-bold text-blue-950 flex items-center gap-2 mb-6">
          <Activity className="w-5 h-5 text-blue-600" /> Biểu đồ Nhiệt độ CPU Edge Node (24h)
        </h3>
        <div className="h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={cpuTempData} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorTemp" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
              <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#94a3b8' }} dy={10} />
              <YAxis domain={['dataMin - 5', 'dataMax + 5']} axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#94a3b8' }} />
              <Tooltip 
                contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 20px rgba(0,0,0,0.1)' }}
                cursor={{ stroke: '#94a3b8', strokeWidth: 1, strokeDasharray: '4 4' }}
              />
              <Area type="monotone" dataKey="temp" stroke="#ef4444" strokeWidth={3} fillOpacity={1} fill="url(#colorTemp)" activeDot={{ r: 6, className: 'cursor-pointer' }} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

    </div>
  );
};

export default HardwareStatus;