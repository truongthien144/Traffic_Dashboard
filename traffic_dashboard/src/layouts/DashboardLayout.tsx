import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, Video, Cpu, Menu, X, Bell, LogOut, Activity
} from 'lucide-react';

const DashboardLayout: React.FC = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const navigation = [
    { name: 'Tổng quan Hệ thống', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Giám sát Nút giao', href: '/dashboard/intersection', icon: Video },
    { name: 'Trạng thái Phần cứng', href: '/dashboard/system', icon: Cpu },
  ];

  const SidebarContent = () => (
    <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-blue-950 px-6 pb-4">
      <div 
        className="flex h-16 shrink-0 items-center gap-3 mt-4 cursor-pointer hover:opacity-80 transition-opacity"
        onClick={() => navigate('/dashboard')}
      >
        <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-700 rounded-xl flex items-center justify-center text-white shadow-lg">
          <Activity className="w-6 h-6" />
        </div>
        <span className="text-2xl font-black text-white">ITS.Core</span>
      </div>
      
      <nav className="flex flex-1 flex-col mt-4">
        <ul role="list" className="flex flex-1 flex-col gap-y-7">
          <li>
            <ul role="list" className="-mx-2 space-y-2">
              {navigation.map((item) => {
                const isActive = location.pathname.includes(item.href) && 
                  (item.href !== '/dashboard' || location.pathname === '/dashboard');
                
                return (
                  <li key={item.name}>
                    <button
                      onClick={() => {
                        navigate(item.href);
                        setIsMobileMenuOpen(false);
                      }}
                      className={`cursor-pointer group flex w-full items-center gap-x-3 rounded-xl p-3 text-sm font-semibold leading-6 transition-all duration-200 ${
                        isActive
                          ? 'bg-blue-600 text-white shadow-md shadow-blue-900/50'
                          : 'text-blue-200 hover:bg-blue-900 hover:text-white'
                      }`}
                    >
                      <item.icon className={`h-6 w-6 shrink-0 ${isActive ? 'text-white' : 'text-blue-400 group-hover:text-white'}`} />
                      {item.name}
                    </button>
                  </li>
                );
              })}
            </ul>
          </li>
        </ul>
      </nav>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-50">
      {/* MOBILE SIDEBAR */}
      {isMobileMenuOpen && (
        <div className="relative z-50 lg:hidden">
          <div className="fixed inset-0 bg-slate-900/80 backdrop-blur-sm transition-opacity" onClick={() => setIsMobileMenuOpen(false)}></div>
          <div className="fixed inset-0 flex">
            <div className="relative mr-16 flex w-full max-w-xs flex-1 transform transition duration-300 ease-in-out">
              <div className="absolute left-full top-0 flex w-16 justify-center pt-5">
                <button type="button" className="-m-2.5 p-2.5 cursor-pointer" onClick={() => setIsMobileMenuOpen(false)}>
                  <X className="h-6 w-6 text-white" />
                </button>
              </div>
              <SidebarContent />
            </div>
          </div>
        </div>
      )}

      {/* DESKTOP SIDEBAR */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-72 lg:flex-col shadow-2xl shadow-blue-900/20">
        <SidebarContent />
      </div>

      {/* MAIN CONTENT AREA */}
      <div className="lg:pl-72 flex flex-col min-h-screen">
        <div className="sticky top-0 z-40 flex h-20 shrink-0 items-center gap-x-4 border-b border-slate-200 bg-white/80 backdrop-blur-md px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
          
          <button type="button" className="-m-2.5 p-2.5 text-slate-700 lg:hidden hover:bg-slate-100 rounded-lg cursor-pointer" onClick={() => setIsMobileMenuOpen(true)}>
            <Menu className="h-6 w-6" />
          </button>

          <div className="flex flex-1 justify-end gap-x-4 self-stretch lg:gap-x-6">
            <div className="flex items-center gap-x-4 lg:gap-x-6">
              <button type="button" className="-m-2.5 p-2.5 text-slate-400 hover:text-blue-600 transition-colors relative cursor-pointer">
                <Bell className="h-6 w-6" />
                <span className="absolute top-2 right-2.5 h-2.5 w-2.5 rounded-full bg-red-500 ring-2 ring-white"></span>
              </button>

              <div className="hidden lg:block lg:h-6 lg:w-px lg:bg-slate-200" aria-hidden="true" />
              
              {/* NÚT ĐĂNG XUẤT ĐÃ ĐƯỢC CHÈN LOGIC XÓA TOKEN */}
              <button 
                onClick={() => {
                  localStorage.removeItem('its_token'); // Xóa token xác thực
                  navigate('/'); // Chuyển hướng về trang chính
                }}
                className="flex items-center gap-2 p-2 text-sm font-semibold leading-6 text-slate-700 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer"
              >
                <div className="h-9 w-9 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold border border-blue-200">
                  AD
                </div>
                <span className="hidden lg:flex lg:items-center">Admin</span>
                <LogOut className="w-5 h-5 ml-2 text-slate-400 hover:text-red-500 transition-colors" />
              </button>
            </div>
          </div>
        </div>

        <main className="flex-1 p-4 sm:p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;