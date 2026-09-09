import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { 
  ArrowLeft, Activity, Zap, Clock, Maximize2, Minimize2, BarChart3, 
  ListOrdered, Car, Bike, Truck
} from 'lucide-react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';

const IntersectionAnalytics: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const currentId = id || "1";

  const [isFullscreen, setIsFullscreen] = useState(false);
  const [intersectionName, setIntersectionName] = useState("Đang tải...");

  const [liveEvents, setLiveEvents] = useState<any[]>([]);
  const [vehicleTypesData, setVehicleTypesData] = useState([
    { name: 'Xe máy', value: 0, color: '#3b82f6' }, 
    { name: 'Ô tô', value: 0, color: '#10b981' },   
    { name: 'Xe tải', value: 0, color: '#f59e0b' },   
    { name: 'Xe buýt', value: 0, color: '#6366f1' },  
  ]);

  const [pcuTrendData, setPcuTrendData] = useState<{ time: string, pcu: number }[]>([]);

  // ===== State điều khiển =====
  const [tGreenMain, setTGreenMain] = useState(30);
  const [tGreenCross, setTGreenCross] = useState(30);
  const [mode, setMode] = useState<"adaptive" | "fixed">("fixed");
  const [pcuMain, setPcuMain] = useState(0);
  const [pcuCross, setPcuCross] = useState(0);
  const [lastUpdate, setLastUpdate] = useState<number>(Date.now());

  // ===== Fetch dữ liệu từ Backend =====
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`http://192.168.101.82:8000/api/traffic_stats/${currentId}`);
        const data = await response.json();
	const serverLastUpdate = data.last_update ? data.last_update * 1000 : 0; // đổi sang ms
	setLastUpdate(serverLastUpdate);
        setIntersectionName(data.name);
        //setLastUpdate(Date.now());

        // Events
        const mappedEvents = data.events.map((ev: any) => {
          let icon = Car; let color = 'text-emerald-500'; let bg = 'bg-emerald-50';
          if (ev.vehicle_type === 'Motorcycle') { icon = Bike; color = 'text-blue-500'; bg = 'bg-blue-50'; }
          else if (ev.vehicle_type === 'Truck') { icon = Truck; color = 'text-amber-500'; bg = 'bg-amber-50'; }
          else if (ev.vehicle_type === 'Bus') { icon = Truck; color = 'text-indigo-500'; bg = 'bg-indigo-50'; }
          return { ...ev, icon, color, bg };
        });
        setLiveEvents(mappedEvents);

        // Vehicle counts
        const cars = (data.counts_main["0"] || 0) + (data.counts_cross["0"] || 0);
        const buses = (data.counts_main["1"] || 0) + (data.counts_cross["1"] || 0);
        const trucks = (data.counts_main["2"] || 0) + (data.counts_cross["2"] || 0);
        const motos = (data.counts_main["3"] || 0) + (data.counts_cross["3"] || 0);

        setVehicleTypesData([
          { name: 'Xe máy', value: motos, color: '#3b82f6' },
          { name: 'Ô tô', value: cars, color: '#10b981' },
          { name: 'Xe tải', value: trucks, color: '#f59e0b' },
          { name: 'Xe buýt', value: buses, color: '#6366f1' },
        ]);

        // ===== Dữ liệu thật từ Backend =====
        const pcuMainVal = Number(data.pcu_main ?? 0);
        const pcuCrossVal = Number(data.pcu_cross ?? 0);
		// Kiểm tra dữ liệu còn mới không
	const secondsSinceUpdate = (Date.now() - serverLastUpdate) / 1000;

        setPcuMain(pcuMainVal);
        setPcuCross(pcuCrossVal);
// ===== Tự chuyển Fixed khi mất tín hiệu sau 10s =====
        setLastUpdate(serverLastUpdate || Date.now());
setTGreenMain(data.t_green_main ?? 30);
setTGreenCross(data.t_green_cross ?? 30);
setMode(data.mode === "adaptive" ? "adaptive" : "fixed");

        // Trend chart (dùng tổng để vẽ biểu đồ)
        const nowTime = new Date().toLocaleTimeString('vi-VN', { 
          hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' 
        });
        setPcuTrendData(prev => {
          const newData = [...prev, { time: nowTime, pcu: Number((pcuMainVal + pcuCrossVal).toFixed(1)) }];
          if (newData.length > 8) newData.shift();
          return newData;
        });

      } catch (error) {
        console.error("Lỗi khi đồng bộ dữ liệu AI:", error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);
  }, [currentId]);

  
  

  return (
    <div className="animate-in fade-in slide-in-from-right-4 duration-700 ease-out max-w-[1600px] mx-auto">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => navigate('/dashboard')}
            className="p-2.5 bg-white border border-slate-200 text-slate-500 hover:text-blue-600 hover:border-blue-200 hover:bg-blue-50 rounded-xl transition-all cursor-pointer shadow-sm active:scale-95"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-xl sm:text-2xl font-extrabold text-blue-950 tracking-tight">{intersectionName}</h1>
              <span className="px-2.5 py-1 bg-emerald-50 text-emerald-600 border border-emerald-100 rounded-md text-[10px] sm:text-xs font-bold flex items-center gap-1.5 cursor-default">
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                YOLO26 Active
              </span>
            </div>
            <p className="text-slate-500 font-medium text-xs sm:text-sm">
              ID: INT-0{currentId} | Camera: Cam-AI-0{currentId} (1080p, 30fps)
            </p>
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-6">
        
        {/* Video */}
        <div className={
          isFullscreen 
            ? "fixed inset-0 z-[100] bg-slate-950 p-4 sm:p-12 md:p-16 flex items-center justify-center animate-in fade-in zoom-in-95 duration-200" 
            : "w-full bg-white p-2 rounded-2xl border border-slate-200 shadow-sm relative overflow-hidden group"
        }>
          <div className={`absolute z-10 flex justify-between items-center pointer-events-none ${isFullscreen ? 'top-4 left-4 right-4 sm:top-6 sm:left-6 sm:right-6' : 'top-4 left-4 right-4'}`}>
            <div className="bg-black/60 backdrop-blur-md px-3 sm:px-4 py-1.5 sm:py-2 rounded-xl border border-white/10 flex items-center gap-2 sm:gap-3 shadow-2xl">
              <div className="flex items-center gap-1.5 sm:gap-2">
                <div className="w-2 h-2 sm:w-2.5 sm:h-2.5 bg-red-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(239,68,68,0.8)]"></div>
                <span className="text-red-400 font-bold text-[10px] sm:text-xs tracking-widest">LIVE</span>
              </div>
              <div className="w-px h-3.5 bg-white/20"></div>
              <span className="text-slate-300 font-mono text-[10px] sm:text-xs font-semibold tracking-wider">INT-0{currentId}</span>
            </div>
            
            <button 
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-2 sm:p-2.5 bg-black/60 backdrop-blur-md border border-white/10 text-white rounded-xl hover:bg-blue-600 transition-all pointer-events-auto cursor-pointer shadow-2xl hover:scale-105 active:scale-95"
            >
              {isFullscreen ? <Minimize2 className="w-5 h-5 sm:w-6 sm:h-6" /> : <Maximize2 className="w-4 h-4 sm:w-5 sm:h-5" />}
            </button>
          </div>

          <div className={`relative w-full bg-slate-900 flex items-center justify-center overflow-hidden border border-slate-800/50 shadow-2xl ${isFullscreen ? 'h-full rounded-2xl' : 'aspect-[4/3] sm:aspect-video md:aspect-[21/9] rounded-xl'}`}>
            <img 
              src={`http://192.168.101.82:8000/api/video_feed/${currentId}`} 
              alt="Live Traffic AI Camera"
              className="w-full h-full object-contain"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Cột trái */}
          <div className="flex flex-col gap-6 h-full">
            <div className="grid grid-cols-2 gap-4 sm:gap-6">
              
              {/* Card Thời gian xanh + Mode */}
              <div className="bg-white p-4 sm:p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between cursor-default">
                <div>
                  <p className="text-[10px] sm:text-xs font-bold text-slate-500 mb-1">
                    Thời gian xanh (Main / Cross)
                  </p>
                  <div className="flex items-baseline gap-2">
                    <h3 className="text-2xl sm:text-3xl font-black text-blue-600">
                      {tGreenMain}<span className="text-sm">s</span>
                    </h3>
                    <span className="text-slate-400">/</span>
                    <h3 className="text-2xl sm:text-3xl font-black text-indigo-600">
                      {tGreenCross}<span className="text-sm">s</span>
                    </h3>
                  </div>
                  <p className="text-[10px] mt-1 font-semibold">
                    Mode:{" "}
                    <span className={mode === "adaptive" ? "text-emerald-600" : "text-amber-600"}>
                      {mode === "adaptive" ? "Adaptive" : "Fixed-time"}
                    </span>
                  </p>
                </div>
                <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-blue-50 border-[3px] border-blue-500 flex items-center justify-center">
                  <span className="text-blue-600 font-black text-xs sm:text-sm">Go</span>
                </div>
              </div>

              {/* Card kết nối */}
              <div className="bg-white p-4 sm:p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-center cursor-default">
                <p className="text-[10px] sm:text-xs font-bold text-slate-500 mb-2 flex items-center gap-1.5 whitespace-nowrap">
                  <Zap className="w-3.5 h-3.5 text-amber-500" /> Kết nối YOLO26
                </p>
                <div className="flex items-center gap-3">
                  <div className="flex-1 bg-slate-100 h-2 rounded-full overflow-hidden">
                    <div className="bg-emerald-500 h-full w-[100%] rounded-full animate-pulse"></div>
                  </div>
                  <span className="text-[10px] sm:text-xs font-bold text-emerald-600">Syncing</span>
                </div>
              </div>
            </div>

            {/* Nhật ký AI */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col h-[350px] lg:h-[480px]">
              <div className="px-4 sm:px-5 py-3 sm:py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50 shrink-0 rounded-t-2xl">
                <h3 className="font-bold text-sm sm:text-base text-blue-950 flex items-center gap-2">
                  <ListOrdered className="w-4 h-4 sm:w-5 sm:h-5 text-blue-600" /> Nhật ký AI (Real-time)
                </h3>
              </div>
              
              <div className="flex-1 overflow-y-auto p-2">
                <ul className="space-y-1">
                  {!liveEvents || liveEvents.length === 0 ? (
                    <div className="text-center text-slate-400 py-10 font-medium flex flex-col items-center justify-center h-full">
                      <div className="w-12 h-12 rounded-full bg-slate-50 flex items-center justify-center mb-2 border border-slate-100">
                        <Clock className="w-6 h-6 text-slate-300" />
                      </div>
                      Đang chờ phương tiện...
                    </div>
                  ) : (
                    liveEvents.map((log, index) => (
                      <li key={log.id || index} className="flex items-center gap-2 sm:gap-3 p-2 sm:p-3 hover:bg-slate-50 rounded-xl transition-colors cursor-default">
                        <span className="text-[10px] sm:text-[11px] font-mono font-semibold text-slate-400 shrink-0">{log.time}</span>
                        <div className={`w-7 h-7 sm:w-8 sm:h-8 rounded-full ${log.bg} ${log.color} flex items-center justify-center shrink-0`}>
                          <log.icon className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                        </div>
                        <div className="flex-1">
                          <p className="text-xs sm:text-sm font-bold text-slate-700 leading-tight">{log.message}</p>
                          <p className="text-[10px] sm:text-xs font-medium text-slate-500 flex items-center gap-2 mt-1">
                            <span className={`px-1.5 py-0.5 rounded-md font-bold ${
                              log.vehicle_type === 'Car' ? 'bg-emerald-100 text-emerald-700' :
                              log.vehicle_type === 'Motorcycle' ? 'bg-blue-100 text-blue-700' :
                              'bg-amber-100 text-amber-700'
                            }`}>
                              {log.vehicle_type}
                            </span>
                            {log.conf && (
                              <>
                                <span>•</span>
                                <span>Conf: <span className="text-emerald-600 font-bold">{log.conf}</span></span>
                              </>
                            )}
                          </p>
                        </div>
                      </li>
                    ))
                  )}
                </ul>
              </div>
            </div>
          </div>

          {/* Cột phải */}
          <div className="flex flex-col gap-6 h-full">
            
            <div className="grid grid-cols-2 gap-4 sm:gap-6">
              {/* Card PCU Main / Cross */}
              <div className="bg-blue-950 p-4 sm:p-5 rounded-2xl shadow-sm cursor-default flex flex-col justify-between relative overflow-hidden">
                <div className="absolute top-0 right-0 w-24 h-24 sm:w-32 sm:h-32 bg-blue-500 rounded-full blur-3xl opacity-20 -mr-10 -mt-10"></div>
                
                <p className="text-blue-200 text-[10px] sm:text-xs font-semibold mb-1 flex items-center gap-1.5 relative z-10">
                  <Activity className="w-3.5 h-3.5 text-blue-400" /> Tải lượng PCU
                </p>

                <div className="relative z-10">
                  <div className="flex items-baseline gap-2">
                    <h4 className="text-white font-black text-2xl sm:text-3xl">
                      {mode === "fixed" ? "--" : pcuMain.toFixed(1)}
                    </h4>
                    <span className="text-blue-300 text-lg font-medium">/</span>
                    <h4 className="text-white font-black text-2xl sm:text-3xl">
                      {mode === "fixed" ? "--" : pcuCross.toFixed(1)}
                    </h4>
                  </div>
                  <p className="text-blue-300 text-xs mt-1 font-medium">
                    Main / Cross
                  </p>
                </div>
              </div>

              {/* Card Tổng lượt xe */}
              <div className="bg-white border border-slate-200 p-4 sm:p-5 rounded-2xl shadow-sm cursor-default flex flex-col justify-between">
                <p className="text-slate-500 text-[10px] sm:text-xs font-bold mb-1 flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-blue-600" /> Tổng Lượt Xe
                </p>
                <h4 className="text-blue-950 font-black text-2xl sm:text-4xl">
                  {vehicleTypesData.reduce((acc, curr) => acc + curr.value, 0)}{" "}
                  <span className="text-xs sm:text-sm font-bold text-slate-400">lượt</span>
                </h4>
              </div>
            </div>

            {/* Biểu đồ biến thiên */}
            <div className="bg-white p-4 sm:p-5 rounded-2xl border border-slate-200 shadow-sm cursor-default flex-1 flex flex-col">
              <h3 className="font-bold text-sm sm:text-base text-blue-950 flex items-center gap-2 mb-4 shrink-0">
                <Activity className="w-4 h-4 text-blue-600" /> Biến thiên Tải lượng
              </h3>
              <div className="flex-1 min-h-[140px] sm:min-h-[160px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={pcuTrendData} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorPcu" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                    <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#94a3b8' }} dy={10} />
                    <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#94a3b8' }} />
                    <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 20px rgba(0,0,0,0.1)' }} />
                    <Area type="monotone" dataKey="pcu" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorPcu)" isAnimationActive={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Phân loại phương tiện */}
            <div className="bg-white p-4 sm:p-5 rounded-2xl border border-slate-200 shadow-sm cursor-default flex-1 flex flex-col">
              <h3 className="font-bold text-sm sm:text-base text-blue-950 flex items-center gap-2 mb-2 shrink-0">
                <BarChart3 className="w-4 h-4 text-blue-600" /> Phân loại Phương tiện
              </h3>
              <div className="flex-1 min-h-[140px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={vehicleTypesData.filter(d => d.value > 0)}
                      cx="50%"
                      cy="50%"
                      innerRadius={40}
                      outerRadius={60}
                      paddingAngle={5}
                      dataKey="value"
                      stroke="none"
                      isAnimationActive={false}
                    >
                      {vehicleTypesData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend iconType="circle" wrapperStyle={{ fontSize: '10px', fontWeight: '600', color: '#64748b' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
};

export default IntersectionAnalytics;