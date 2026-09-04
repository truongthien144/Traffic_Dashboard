import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle2, 
  Car, 
  MapPin, 
  ArrowRight, 
  Zap,
  RefreshCw,
  ServerCrash
} from 'lucide-react';

// Dữ liệu bảng danh sách ngã tư (Sẽ được gọi API động ở các bước sau, tạm thời giữ Mock để hiển thị UI)
const mockIntersections = [
  { 
    id: 'INT-01', 
    name: 'Ngã tư Điện Biên Phủ - Đinh Tiên Hoàng', 
    status: 'online', 
    greenTime: '45s', 
    aiStatus: 'YOLO26-Active', 
    ping: '12ms' 
  },
  { 
    id: 'INT-02', 
    name: 'Ngã tư Phạm Văn Đồng', 
    status: 'online', 
    greenTime: '60s', 
    aiStatus: 'YOLO26-Active', 
    ping: '45ms' 
  },
  { 
    id: 'INT-03', 
    name: 'Ngã tư Nguyễn Hữu Cảnh', 
    status: 'online', 
    greenTime: '60s', 
    aiStatus: 'YOLO26-Active', 
    ping: '25ms' 
  },
];

const DashboardOverview: React.FC = () => {
  const navigate = useNavigate();

  // Khởi tạo State để hứng dữ liệu từ Backend
  const [overviewStats, setOverviewStats] = useState({
    total_intersections: 3,
    active_nodes: 0,
    active_cameras: [] as string[],
    total_pcu: 0,
    total_vehicles_24h: 0,
    system_status: "Đang kết nối..."
  });
const isOffline = overviewStats.system_status === "Mất kết nối";
const activeCameras = overviewStats.active_cameras || [];
  // Gọi API tổng hợp dữ liệu mỗi 2 giây
  useEffect(() => {
    const fetchOverviewStats = async () => {
      try {
        const response = await fetch('http://192.168.101.82:8000/api/overview_stats');
        if (response.ok) {
          const data = await response.json();
          setOverviewStats(data);
        }
      } catch (error) {
        console.error("Lỗi khi kết nối với Backend:", error);
        setOverviewStats(prev => ({ ...prev, system_status: "Mất kết nối" }));
      }
    };

    // Gọi lần đầu ngay khi render
    fetchOverviewStats();
    
    // Thiết lập vòng lặp gọi API
    const interval = setInterval(fetchOverviewStats, 2000);
    return () => clearInterval(interval);
  }, []);

  const getPingColor = (pingStr: string) => {
    if (pingStr === 'Timeout') return 'text-red-500 font-bold';
    const pingValue = parseInt(pingStr.replace(/\D/g, ''));
    if (isNaN(pingValue)) return 'text-slate-500';
    if (pingValue <= 30) return 'text-emerald-500 font-semibold';
    if (pingValue <= 80) return 'text-amber-500 font-semibold';
    return 'text-red-500 font-semibold';
  };

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 ease-out max-w-7xl mx-auto">
      
      {/* HEADER SECTION */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-extrabold text-blue-950 tracking-tight mb-1">Tổng quan Hệ thống</h1>
          <p className="text-slate-500 font-medium">Giám sát tải lượng PCU và tình trạng các nút giao theo thời gian thực.</p>
        </div>
        
        <div className="flex items-center gap-3">
          <div className={`flex items-center gap-2 text-sm font-semibold px-3 py-1.5 rounded-lg border cursor-default ${overviewStats.system_status === 'Mất kết nối' ? 'text-red-600 bg-red-50 border-red-100' : 'text-emerald-600 bg-emerald-50 border-emerald-100'}`}>
            <span className="relative flex h-2.5 w-2.5">
              {overviewStats.system_status !== 'Mất kết nối' && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              )}
              <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${overviewStats.system_status === 'Mất kết nối' ? 'bg-red-500' : 'bg-emerald-500'}`}></span>
            </span>
            {overviewStats.system_status === 'Mất kết nối' ? 'Offline' : 'Live Sync'}
          </div>
          <button className="p-2.5 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors border border-slate-200 hover:border-blue-200 bg-white shadow-sm cursor-pointer active:scale-95">
            <RefreshCw className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* STATS GRID (Bây giờ sử dụng biến State động từ API) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Stat Card 1 */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex justify-between items-start mb-4">
  <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center">
    <MapPin className="w-6 h-6" />
  </div>
  {isOffline ? (
    <span className="text-xs font-bold text-red-600 bg-red-50 px-2 py-1 rounded-md">Offline</span>
  ) : (
    <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded-md">Online</span>
  )}
</div>
          <p className="text-sm font-bold text-slate-500 mb-1">Nút giao Hoạt động</p>
          <div className="flex items-baseline gap-1">
            <h3 className="text-3xl font-bold text-blue-950">{overviewStats.active_nodes}</h3>
            <span className="text-lg font-medium text-slate-400">/{overviewStats.total_intersections}</span>
          </div>
        </div>

        {/* Stat Card 2 */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex justify-between items-start mb-4">
            <div className="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center">
              <Car className="w-6 h-6" />
            </div>
          </div>
          <p className="text-sm font-bold text-slate-500 mb-1">Tổng Lượt Phương Tiện</p>
          <div className="flex items-baseline">
            {/* Đổ dữ liệu động tổng số xe */}
            <h3 className="text-3xl font-bold text-blue-950">{overviewStats.total_vehicles_24h.toLocaleString()}</h3>
          </div>
        </div>

        {/* Stat Card 3 */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex justify-between items-start mb-4">
            <div className="w-12 h-12 bg-amber-50 text-amber-600 rounded-xl flex items-center justify-center">
              <Activity className="w-6 h-6" />
            </div>
            {overviewStats.total_pcu > 10 ? (
              <span className="text-xs font-bold text-amber-600 bg-amber-50 px-2 py-1 rounded-md">Đông đúc</span>
            ) : (
              <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded-md">Thông thoáng</span>
            )}
          </div>
          <p className="text-sm font-bold text-slate-500 mb-1">Tổng Tải Lượng PCU</p>
          <div className="flex items-baseline gap-1.5">
            {/* Đổ dữ liệu động tổng PCU */}
            <h3 className="text-3xl font-bold text-blue-950">{overviewStats.total_pcu.toLocaleString()}</h3>
            <span className="text-sm font-medium text-slate-400">PCU</span>
          </div>
        </div>

        {/* Stat Card 4 */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex justify-between items-start mb-4">
            <div className="w-12 h-12 bg-emerald-50 text-emerald-600 rounded-xl flex items-center justify-center">
              <Zap className="w-6 h-6" />
            </div>
            <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded-md">ESP32-S3</span>
          </div>
          <p className="text-sm font-bold text-slate-500 mb-1">Trạng thái Edge Node</p>
          <div className="flex flex-col">
            <h3 className={`text-xl font-bold ${overviewStats.system_status === 'Mất kết nối' ? 'text-red-500' : 'text-blue-950'}`}>
              {overviewStats.system_status}
            </h3>
            <span className="text-xs font-medium text-slate-400">Mạch Rasberry Pi</span>
          </div>
        </div>
      </div>

      {/* INTERSECTION LIST */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-5 border-b border-slate-200 flex justify-between items-center bg-slate-50/50">
          <h2 className="text-lg font-bold text-blue-950 flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-600" />
            Tình trạng Trạm điều khiển
          </h2>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-white border-b border-slate-100 text-sm">
                <th className="px-6 py-4 font-bold text-slate-500 uppercase tracking-wider">Tên nút giao</th>
                <th className="px-6 py-4 font-bold text-slate-500 uppercase tracking-wider">Trạng thái</th>
                <th className="px-6 py-4 font-bold text-slate-500 uppercase tracking-wider">Đèn xanh Tối ưu</th>
                <th className="px-6 py-4 font-bold text-slate-500 uppercase tracking-wider">Module AI</th>
                <th className="px-6 py-4 font-bold text-slate-500 uppercase tracking-wider text-right">Hành động</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {mockIntersections.map((node) => (
                <tr key={node.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="font-bold text-blue-950 mb-0.5">{node.name}</div>
                    <div className="text-xs text-slate-400 font-medium font-mono">{node.id}</div>
                  </td>
                  
                   <td className="px-6 py-4">
                    {isOffline || !activeCameras.includes(node.id.replace('INT-0', '')) ? (
                     <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold bg-slate-100 text-slate-500 border border-slate-200">
                      <AlertTriangle className="w-3.5 h-3.5" /> Tạm dừng
                     </span>
                   ) : (
                     <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold bg-emerald-50 text-emerald-600 border border-emerald-100">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Hoạt động
                     </span>
                   )}
                   </td>
                  
                  <td className="px-6 py-4">
                    <div className="text-lg font-bold text-blue-600">
                      {node.greenTime}
                    </div>
                  </td>
                  
                  <td className="px-6 py-4">
                    <div className="flex flex-col gap-1">
                      <span className="text-sm font-semibold text-slate-700">{node.aiStatus}</span>
                      <span className="text-xs text-slate-500 font-medium">
                        Ping: <span className={getPingColor(node.ping)}>{node.ping}</span>
                      </span>
                    </div>
                  </td>
                  
                  <td className="px-6 py-4 text-right">
                    <button 
                      onClick={() => {
                        const routeId = node.id.replace('INT-0', '');
                        navigate(`/dashboard/intersection/${routeId}`);
                      }}
                      className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg hover:bg-blue-50 hover:text-blue-600 hover:border-blue-200 transition-all font-semibold text-sm cursor-pointer group"
                    >
                      Giám sát
                      <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      
    </div>
  );
};

export default DashboardOverview;