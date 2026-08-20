import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, Lock, ArrowLeft } from 'lucide-react';
import { useTranslation } from 'react-i18next'; 

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation(); 
  const [loading, setLoading] = useState<boolean>(false);
  const [mounted, setMounted] = useState(false);

  // Kích hoạt hiệu ứng xuất hiện sau khi Component render
  useEffect(() => {
    setMounted(true);
  }, []);

  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    
    // Lấy giá trị từ các ô input
    const email = (e.currentTarget.elements[0] as HTMLInputElement).value;
    const password = (e.currentTarget.elements[1] as HTMLInputElement).value;

    try {
      const response = await fetch('http://localhost:8000/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      const data = await response.json();

      if (response.ok) {
        // Đăng nhập thành công -> Lưu token vào localStorage
        localStorage.setItem('its_token', data.access_token);
        navigate('/dashboard');
      } else {
        // Báo lỗi sử dụng đa ngôn ngữ
        alert(data.detail || t('login.alert_fail'));
      }
    } catch (error) {
      console.error("Lỗi kết nối server:", error);
      alert(t('login.alert_error')); // <-- Báo lỗi server bằng đa ngôn ngữ
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 selection:bg-blue-300 relative overflow-hidden">
      
      {/* Background Image mang phong cách giao thông ITS */}
      <div 
        className="absolute inset-0 -z-20 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: "url('https://images.unsplash.com/photo-1597762333765-cbcd63dd8acc?q=80&w=736&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D')" }}
      ></div>
      
      {/* Overlay tối màu có blur nhẹ để form nổi bật */}
      <div className="absolute inset-0 -z-10 bg-slate-900/60 backdrop-blur-[4px]"></div>

      {/* Nút Back */}
      <button 
        onClick={() => navigate('/')}
        className="absolute top-8 left-8 cursor-pointer text-white/70 hover:text-white font-semibold transition-all flex items-center gap-2 hover:-translate-x-1"
      >
        <ArrowLeft className="w-5 h-5" /> {t('login.back')}
      </button>

      {/* Khung Đăng nhập */}
      <div className={`w-full max-w-md bg-white/95 backdrop-blur-2xl rounded-[2rem] p-10 border border-white/20 shadow-[0_0_40px_rgba(0,0,0,0.3)] transition-all duration-700 ease-out ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-12'}`}>
        
        <div className="text-center mb-10">
          <div className="w-20 h-20 bg-gradient-to-br from-blue-50 to-blue-100 rounded-3xl mx-auto flex items-center justify-center mb-6 shadow-inner border border-blue-200/50">
            <Lock className="w-10 h-10 text-blue-600" />
          </div>
          <h2 className="text-4xl font-extrabold text-slate-900 mb-3 tracking-tight">{t('login.title')}</h2>
          <p className="text-slate-500 font-medium">{t('login.subtitle')}</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          <div className="group">
            <label className="block text-sm font-bold text-slate-700 mb-2 group-focus-within:text-blue-600 transition-colors">
              {t('login.email_label')}
            </label>
            <input 
              type="text" 
              required
              className="w-full px-5 py-4 rounded-2xl bg-slate-50/50 border border-slate-200 text-slate-900 focus:outline-none focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/15 transition-all font-medium"
              placeholder="admin@gmail.com"
            />
          </div>

          <div className="group">
            <label className="block text-sm font-bold text-slate-700 mb-2 group-focus-within:text-blue-600 transition-colors">
              {t('login.password_label')}
            </label>
            <input 
              type="password" 
              required
              className="w-full px-5 py-4 rounded-2xl bg-slate-50/50 border border-slate-200 text-slate-900 focus:outline-none focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/15 transition-all font-medium"
              placeholder="••••••••"
            />
          </div>

          <button 
            type="submit" 
            disabled={loading}
            className="w-full py-4 bg-gradient-to-r cursor-pointer from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white rounded-2xl font-bold text-base transition-all disabled:opacity-70 shadow-lg shadow-blue-600/30 hover:shadow-blue-600/50 hover:-translate-y-0.5 mt-2 flex justify-center items-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {t('login.authenticating')}
              </>
            ) : t('login.submit_btn')}
          </button>
        </form>
      </div>

      {/* Footer */}
      <div className={`mt-8 flex items-center gap-2 text-white/70 text-sm font-medium transition-all duration-700 delay-300 ${mounted ? 'opacity-100' : 'opacity-0'}`}>
        <Activity className="w-4 h-4 text-blue-400" />
        {t('login.footer')}
      </div>
    </div>
  );
};

export default LoginPage;