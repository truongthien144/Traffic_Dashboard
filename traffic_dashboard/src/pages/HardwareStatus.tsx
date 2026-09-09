import React, { useState, useEffect } from 'react';
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

  const [env, setEnv] = useState<{
    temperature: number | null;
    humidity: number | null;
    last_update: string | null;
  }>({
    temperature: null,
    humidity: null,
    last_update: null,
  });
  // ===== Thêm state riêng cho môi trường =====
const [envLost, setEnvLost] = useState(true);
  // true = đang Fixed / mất dữ liệu → hiển thị "--"
  const [isDataLost, setIsDataLost] = useState(false);

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => setIsRefreshing(false), 1000);
  };
  const [sysStats, setSysStats] = useState({
  cpu_percent: 0,
  ram_used_gb: 0,
  ram_total_gb: 4,
  ram_percent: 0,
  disk_percent: 0,
  cpu_temp: null as number | null,
  uptime: "00:00:00",
  tx_packets: 0,
  rx_packets: 0,
});

// Lịch sử nhiệt độ CPU để vẽ chart (giữ 12 điểm gần nhất)
const [cpuTempHistory, setCpuTempHistory] = useState<{ time: string; temp: number }[]>([]);

useEffect(() => {
  const fetchSysStats = async () => {
    try {
      const res = await fetch("http://192.168.101.82:8000/api/system_stats"); // ← IP Pi của bạn
      if (res.ok) {
        const data = await res.json();
        setSysStats(data);

        // Cập nhật lịch sử nhiệt độ CPU
        if (data.cpu_temp !== null) {
          const nowTime = new Date().toLocaleTimeString("vi-VN", {
            hour12: false,
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
          });
          setCpuTempHistory(prev => {
            const newData = [...prev, { time: nowTime, temp: data.cpu_temp }];
            if (newData.length > 12) newData.shift();
            return newData;
          });
        }
      }
    } catch (e) {
      console.error("Lỗi lấy system stats:", e);
    }
  };

  fetchSysStats();
  const interval = setInterval(fetchSysStats, 3000);
  return () => clearInterval(interval);
}, []);
  // Lấy dữ liệu DHT20
  useEffect(() => {
    const fetchEnv = async () => {
      try {
        const res = await fetch("http://192.168.101.82:8000/api/environment");
        if (res.ok) {
          const data = await res.json();
          setEnv({
            temperature: data.temperature,
            humidity: data.humidity,
            last_update: data.last_update ?? null,
          });
        }
      } catch (e) {
        console.error(e);
      }
    };

    fetchEnv();
    const interval = setInterval(fetchEnv, 5000);
    return () => clearInterval(interval);
  }, []);

  // Kiểm tra mode Fixed + dữ liệu môi trường có cũ không
  useEffect(() => {
  const checkStatus = async () => {
    try {
      // 1. Kiểm tra AI / Control (chỉ dùng cho trạng thái ESP)
      const res = await fetch("http://192.168.101.82:8000/api/traffic_stats/1");
      let fixedFromMode = false;
      let staleControl = false;

      if (res.ok) {
        const data = await res.json();
        fixedFromMode = data.mode === "fixed";

        if (data.last_update) {
          const seconds = (Date.now() - data.last_update * 1000) / 1000;
          staleControl = seconds > 120;
        } else {
          staleControl = true;
        }
      } else {
        staleControl = true;
      }

      setIsDataLost(fixedFromMode || staleControl);

      // 2. Kiểm tra DHT20 riêng
      let staleEnv = true;
      if (env.last_update) {
        const envTime = new Date(env.last_update).getTime();
        const seconds = (Date.now() - envTime) / 1000;
        staleEnv = seconds > 30;
      }
      setEnvLost(staleEnv);

    } catch (e) {
      setIsDataLost(true);
      setEnvLost(true);
    }
  };

  checkStatus();
  const interval = setInterval(checkStatus, 3000);
  return () => clearInterval(interval);
}, [env.last_update]);

  // Giá trị hiển thị
  const displayTemp = envLost || env.temperature === null ? "--" : env.temperature;
const displayHumi = envLost || env.humidity === null ? "--" : `${env.humidity}%`;

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
            <h3 className="text-3xl font-black text-blue-950">{sysStats.cpu_percent}<span className="text-lg text-slate-400 font-bold">%</span></h3>
          </div>
          <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
            <div 
  className="bg-amber-500 h-full rounded-full transition-all duration-500" 
  style={{ width: `${sysStats.cpu_percent}%` }}
></div>
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
            <h3 className="text-3xl font-black text-blue-950">{sysStats.ram_used_gb}<span className="text-lg text-slate-400 font-bold">/{sysStats.ram_total_gb} GB</span></h3>
          </div>
          <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
            <div 
  className="bg-indigo-500 h-full rounded-full transition-all duration-500" 
  style={{ width: `${sysStats.ram_percent}%` }}
></div>
          </div>
        </div>

        {/* DHT20 - Nhiệt độ & Độ ẩm */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm cursor-default hover:border-blue-200 transition-colors">
          <div className="flex justify-between items-start mb-4">
            <div className="w-10 h-10 bg-red-50 text-red-600 rounded-lg flex items-center justify-center">
              <Thermometer className="w-5 h-5" />
            </div>

            {envLost ? (
  <span className="text-xs font-bold text-amber-600 bg-amber-50 px-2 py-1 rounded-md border border-amber-100 flex items-center gap-1">
    <AlertCircle className="w-3 h-3" /> Mất dữ liệu
  </span>
) : env.temperature !== null && env.temperature > 35 ? (
  <span className="text-xs font-bold text-red-600 bg-red-50 px-2 py-1 rounded-md border border-red-100 flex items-center gap-1">
    <AlertCircle className="w-3 h-3" /> Cao
  </span>
) : (
  <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded-md border border-emerald-100">
    Bình thường
  </span>
)}
          </div>

          <p className="text-xs font-bold text-slate-500 mb-1 uppercase tracking-wider">
            Nhiệt độ môi trường (DHT20)
          </p>

          <div className="flex items-baseline gap-2 mb-1">
            <h3 className="text-3xl font-black text-blue-950">
              {displayTemp}
              <span className="text-lg text-slate-400 font-bold">°C</span>
            </h3>
          </div>

          <p className="text-sm text-slate-500">
            Độ ẩm:{" "}
            <span className="font-bold text-blue-600">
              {displayHumi}
            </span>
          </p>
        </div>

        {/* Storage / SD Card */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm cursor-default hover:border-blue-200 transition-colors">
          <div className="flex justify-between items-start mb-4">
            <div className="w-10 h-10 bg-emerald-50 text-emerald-600 rounded-lg flex items-center justify-center">
              <HardDrive className="w-5 h-5" />
            </div>
            <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded-md border border-emerald-100">Healthy</span>
          </div>
          <p className="text-xs font-bold text-slate-500 mb-1 uppercase tracking-wider">Storage (micro-SD Card: 64GB)</p>
          <div className="flex items-baseline gap-2 mb-3">
            <h3 className="text-3xl font-black text-blue-950">{sysStats.disk_percent}<span className="text-lg text-slate-400 font-bold">%</span></h3>
          </div>
          <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
            <div 
  className="bg-emerald-500 h-full rounded-full transition-all duration-500" 
  style={{ width: `${sysStats.disk_percent}%` }}
></div>
          </div>
        </div>
      </div>

      {/* SECTION 2: MCU (ESP32) */}
      <h2 className="text-lg font-bold text-blue-950 mb-4 flex items-center gap-2 mt-10">
        <Zap className="w-5 h-5 text-amber-500" /> Vi điều khiển ESP32
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-center cursor-default">
  <div className="flex items-center justify-between mb-4">
    <div className={`w-10 h-10 rounded-lg flex items-center justify-center shadow-sm ${
      isDataLost 
        ? "bg-red-50 text-red-600" 
        : "bg-emerald-50 text-emerald-600"
    }`}>
      {isDataLost ? <AlertCircle className="w-5 h-5" /> : <CheckCircle2 className="w-5 h-5" />}
    </div>
    
    {isDataLost ? (
      <span className="text-xs font-bold text-red-600 bg-red-50 px-2.5 py-1 rounded-md border border-red-100">
        Offline
      </span>
    ) : (
      <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-100">
        Online
      </span>
    )}
  </div>
  
  <p className="text-xs font-bold text-slate-500 mb-1 uppercase tracking-wider">Trạng thái Giao tiếp</p>
  
  <h3 className={`text-2xl font-black mb-1 ${isDataLost ? "text-red-500" : "text-blue-950"}`}>
    {isDataLost ? "Mất kết nối" : "Ổn định"}
  </h3>
  
  <p className="text-sm font-medium text-slate-400">
    {isDataLost ? "Không có phản hồi" : "Độ trễ phản hồi: 12ms"}
  </p>
</div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-center cursor-default">
          <div className="flex items-center justify-between mb-4">
            <div className="w-10 h-10 bg-blue-50 text-blue-600 rounded-lg flex items-center justify-center shadow-sm">
              <Clock className="w-5 h-5" />
            </div>
          </div>
          <p className="text-xs font-bold text-slate-500 mb-1 uppercase tracking-wider">Thời gian Hoạt động</p>
          <h3 className="text-2xl font-black text-blue-950 mb-1">{sysStats.uptime}</h3>
          <p className="text-sm font-medium text-slate-400">Giờ : Phút : Giây</p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-center cursor-default">
          <div className="flex items-center justify-between mb-4">
            <div className="w-10 h-10 bg-indigo-50 text-indigo-600 rounded-lg flex items-center justify-center shadow-sm">
              <ArrowRightLeft className="w-5 h-5" />
            </div>
          </div>
          <p className="text-xs font-bold text-slate-500 mb-1 uppercase tracking-wider">Lưu lượng Dữ liệu</p>
          <h3 className="text-2xl font-black text-blue-950 mb-1">{`${sysStats.tx_packets} / ${sysStats.rx_packets}`}</h3>
          <p className="text-sm font-medium text-slate-400">Packets (Tx / Rx)</p>
        </div>
      </div>

      {/* SECTION 3: SYSTEM CHARTS */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm cursor-default">
  <h3 className="font-bold text-blue-950 flex items-center gap-2 mb-6">
    <Activity className="w-5 h-5 text-blue-600" /> 
    Biểu đồ Nhiệt độ CPU Edge Node
  </h3>
  
  <div className="h-[250px]">
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={cpuTempHistory} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
        <defs>
          <linearGradient id="colorTemp" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#ef4444" stopOpacity={0.35}/>
            <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
        <XAxis 
          dataKey="time" 
          axisLine={false} 
          tickLine={false} 
          tick={{ fontSize: 11, fill: '#94a3b8' }} 
          dy={8}
        />
        <YAxis 
          domain={[30, 85]}          // ← độ chia dễ nhìn hơn (30°C → 85°C)
          axisLine={false} 
          tickLine={false} 
          tick={{ fontSize: 11, fill: '#94a3b8' }}
          tickFormatter={(v) => `${v}°`}
        />
        <Tooltip 
          contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 20px rgba(0,0,0,0.1)' }}
          formatter={(value: number) => [`${value} °C`, "Nhiệt độ CPU"]}
        />
        <Area 
          type="monotone" 
          dataKey="temp" 
          stroke="#ef4444" 
          strokeWidth={3} 
          fillOpacity={1} 
          fill="url(#colorTemp)" 
          isAnimationActive={false}
          activeDot={{ r: 6 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  </div>
</div>

    </div>
  );
};

export default HardwareStatus;