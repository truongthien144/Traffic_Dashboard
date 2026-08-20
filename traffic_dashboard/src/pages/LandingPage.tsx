import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { 
  Activity, Cpu, ArrowRight, MapPin, 
  BarChart3, Clock, Camera, Zap, Server, 
  LayoutDashboard, Globe, ChevronUp 
} from 'lucide-react';

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const [showScrollTop, setShowScrollTop] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setShowScrollTop(window.scrollY > 300);
    };
    window.addEventListener('scroll', handleScroll);

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('opacity-100', 'translate-y-0');
          entry.target.classList.remove('opacity-0', 'translate-y-12');
        }
      });
    }, { threshold: 0.1 });

    document.querySelectorAll('.scroll-reveal').forEach(el => observer.observe(el));

    return () => {
      window.removeEventListener('scroll', handleScroll);
      observer.disconnect();
    };
  }, []);

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const toggleLanguage = () => {
    const nextLang = i18n.language === 'vi' ? 'en' : 'vi';
    i18n.changeLanguage(nextLang);
  };

  const workflowSteps = [ 
    { icon: Camera, title: t('landing.workflow.step1_title'), desc: t('landing.workflow.step1_desc'), color: 'from-blue-500 to-cyan-500', bg: 'bg-blue-50', text: 'text-blue-600' },
    { icon: ScanLineIcon, title: t('landing.workflow.step2_title'), desc: t('landing.workflow.step2_desc'), color: 'from-indigo-500 to-blue-500', bg: 'bg-indigo-50', text: 'text-indigo-600' },
    { icon: BarChart3, title: t('landing.workflow.step3_title'), desc: t('landing.workflow.step3_desc'), color: 'from-purple-500 to-indigo-500', bg: 'bg-purple-50', text: 'text-purple-600' },
    { icon: Cpu, title: t('landing.workflow.step4_title'), desc: t('landing.workflow.step4_desc'), color: 'from-emerald-500 to-teal-500', bg: 'bg-emerald-50', text: 'text-emerald-600' }
  ];

  const featureItems = [ 
    { icon: Server, title: t('landing.features.feat1_title'), desc: t('landing.features.feat1_desc') },
    { icon: Zap, title: t('landing.features.feat2_title'), desc: t('landing.features.feat2_desc') },
    { icon: Clock, title: t('landing.features.feat3_title'), desc: t('landing.features.feat3_desc') }
  ];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 font-sans selection:bg-blue-300 selection:text-blue-900 flex flex-col overflow-x-hidden relative">
      
      <button 
        onClick={scrollToTop}
        className={`fixed bottom-8 right-8 z-50 p-3 bg-blue-600 text-white rounded-full shadow-lg shadow-blue-500/30 hover:bg-blue-700 hover:-translate-y-1 transition-all duration-300 ${showScrollTop ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10 pointer-events-none'}`}
      >
        <ChevronUp className="w-6 h-6" />
      </button>

      <nav className="fixed top-0 w-full z-50 bg-white/85 backdrop-blur-md border-b border-blue-100 transition-all duration-300">
        <div className="container mx-auto px-6 py-4 flex justify-between items-center">
          <div className="text-2xl font-black tracking-tighter text-slate-800 flex items-center gap-2 cursor-pointer" onClick={scrollToTop}>
            <div className="w-9 h-9 bg-gradient-to-br from-blue-500 to-blue-700 rounded-xl flex items-center justify-center text-white shadow-md shadow-blue-500/20">
              <Activity className="w-5 h-5" />
            </div>
            ITS<span className="text-blue-600 mr-0 font-normal">.Core</span>
          </div>
          
          <div className="flex items-center gap-4">
            <button 
              onClick={toggleLanguage}
              className="flex cursor-pointer items-center gap-2 px-3 py-2 text-slate-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors font-semibold uppercase"
            >
              <Globe className="w-5 h-5" />
              {i18n.language}
            </button>

            <button 
              onClick={() => navigate('/login')}
              className="flex cursor-pointer items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white rounded-full font-medium transition-all shadow-md hover:shadow-lg hover:shadow-blue-500/30 hover:-translate-y-0.5"
            >
              <LayoutDashboard className="w-4 h-4" />
              {t('landing.nav.login')}
            </button>
          </div>
        </div>
      </nav>

      <main className="relative pt-32 pb-20 lg:pt-40 lg:pb-28 overflow-hidden bg-blue-100/40">
        <div className="absolute top-0 right-0 -translate-y-12 translate-x-1/4 w-[600px] h-[600px] bg-blue-300/30 rounded-full blur-[100px] -z-10 animate-pulse" style={{animationDuration: '4s'}}></div>
        <div className="absolute top-40 left-0 -translate-x-1/2 w-[500px] h-[500px] bg-sky-200/40 rounded-full blur-[100px] -z-10"></div>
        
        <div className="container mx-auto px-6 grid lg:grid-cols-2 gap-12 items-center">
          <div className="z-10 scroll-reveal opacity-0 translate-y-12 transition-all duration-1000 ease-out">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-50 border border-blue-100 text-blue-600 text-sm font-bold mb-6 shadow-sm">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500 animate-ping"></span>
              {t('landing.hero.badge')}
            </div>
            
            <h1 className="text-5xl lg:text-7xl font-extrabold tracking-tight mb-6 leading-[1.1] text-slate-900">
              {t('landing.hero.title_1')} <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-sky-500">
                {t('landing.hero.title_2')}
              </span>
            </h1>
            
            <p className="text-lg text-slate-600 mb-8 leading-relaxed font-light max-w-lg">
              {t('landing.hero.desc')}
            </p>

            <button 
              onClick={() => navigate('/login')}
              className="cursor-pointer group inline-flex items-center gap-2 px-8 py-4 text-white rounded-full font-bold text-lg bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 transition-all shadow-xl shadow-slate-900/20 hover:shadow-blue-600/30 hover:-translate-y-1"
            >
              {t('landing.hero.btn_dashboard')}
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>

          <div className="relative z-10 lg:h-[600px] rounded-3xl hidden md:block scroll-reveal opacity-0 translate-y-12 transition-all duration-1000 delay-200 ease-out">
            <img 
              src="https://images.unsplash.com/photo-1449824913935-59a10b8d2000?q=80&w=2070&auto=format&fit=crop" 
              alt="City Traffic" 
              className="absolute inset-0 w-full h-full object-cover rounded-3xl shadow-2xl shadow-blue-900/10"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-blue-900/60 to-transparent rounded-3xl"></div>
            
            <div className="absolute -bottom-8 -left-8 bg-white/95 backdrop-blur-sm p-6 rounded-2xl shadow-2xl shadow-blue-900/20 border border-blue-50 animate-bounce" style={{animationDuration: '3s'}}>
              <div className="flex items-center justify-between mb-4 gap-8">
                <div className="text-sm font-bold text-slate-600">{t('landing.hero.widget_title')}</div>
                <div className="flex items-center gap-1 text-blue-600 text-xs font-bold bg-blue-50 px-2.5 py-1 rounded-md">
                  <Activity className="w-3.5 h-3.5" /> Real-time
                </div>
              </div>
              <div className="flex items-end gap-5">
                <div>
                  <div className="text-4xl font-black text-slate-800">17.5</div>
                  <div className="text-xs text-slate-500 mt-1">{t('landing.hero.widget_pcu')}</div>
                </div>
                <div className="w-px h-12 bg-slate-200"></div>
                <div>
                  <div className="text-4xl font-black text-blue-600">39s</div>
                  <div className="text-xs text-blue-600 font-bold mt-1">{t('landing.hero.widget_green_light')}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <section className="bg-slate-50 py-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 mix-blend-overlay"></div>
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>

        <div className="container mx-auto px-6 relative z-10 scroll-reveal opacity-0 translate-y-12 transition-all duration-1000 ease-out">
          <div className="text-center mb-20">
            <h2 className="text-3xl md:text-5xl font-extrabold mb-5 text-slate-900">{t('landing.workflow.title')}</h2>
            <p className="text-slate-600 max-w-2xl mx-auto text-lg">{t('landing.workflow.desc')}</p>
          </div>

          <div className="grid md:grid-cols-4 gap-8 relative">
            <div className="hidden md:block absolute top-12 left-[10%] w-[80%] h-1 bg-gradient-to-r from-blue-100 via-blue-400 to-emerald-100 -translate-y-1/2 z-0 rounded-full"></div>

            {workflowSteps.map((step, idx) => (
              <div key={idx} className="relative z-10 bg-white p-8 rounded-3xl border border-slate-200 text-center hover:-translate-y-3 hover:shadow-2xl hover:shadow-slate-200/50 transition-all duration-300 group">
                <div className={`w-20 h-20 mx-auto rounded-2xl flex items-center justify-center mb-6 shadow-lg bg-gradient-to-br ${step.color} transform group-hover:rotate-6 transition-transform duration-300`}>
                  <step.icon className="w-10 h-10 text-white" />
                </div>
                <h3 className="font-extrabold text-xl mb-3 text-slate-800">{step.title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed font-medium">{step.desc}</p>
                <div className={`absolute bottom-0 left-1/2 -translate-x-1/2 w-0 h-1.5 rounded-t-full bg-gradient-to-r ${step.color} group-hover:w-1/2 transition-all duration-300`}></div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-blue-100/40 py-24 border-t border-blue-100">
        <div className="container mx-auto px-6">
          <div className="flex flex-col md:flex-row items-center gap-16 scroll-reveal opacity-0 translate-y-12 transition-all duration-1000 ease-out">
            <div className="w-full md:w-1/2 group">
              <div className="relative rounded-[2.5rem] p-4 bg-white shadow-[0_20px_60px_-15px_rgba(37,99,235,0.15)] border border-blue-50">
                <div className="relative overflow-hidden rounded-3xl">
                  <img 
                    src="https://images.unsplash.com/photo-1494522855154-9297ac14b55f?q=80&w=2070&auto=format&fit=crop" 
                    alt="Intersection Analysis" 
                    className="w-full object-cover h-[450px] group-hover:scale-105 transition-transform duration-700"
                  />
                  <div className="absolute inset-0 bg-blue-900/10 group-hover:bg-transparent transition-colors duration-700"></div>
                </div>
              </div>
            </div>
            
            <div className="w-full md:w-1/2">
              <h2 className="text-3xl md:text-5xl font-extrabold text-slate-900 mb-6 leading-tight">
                {t('landing.features.title_1')} <br/><span className="text-blue-600">{t('landing.features.title_2')}</span>
              </h2>
              <p className="text-slate-500 mb-10 text-lg leading-relaxed">
                {t('landing.features.desc')}
              </p>
              
              <div className="space-y-8">
                {featureItems.map((feature, idx) => (
                  <div key={idx} className="flex gap-5 hover:translate-x-2 transition-transform duration-300 cursor-default p-1 rounded-2xl hover:bg-white hover:shadow-xl hover:shadow-blue-900/5 border border-transparent hover:border-blue-50">
                    <div className="w-14 h-14 shrink-0 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center shadow-inner border border-blue-100">
                      <feature.icon className="w-6 h-6" />
                    </div>
                    <div>
                      <h4 className="font-bold text-xl text-slate-900 mb-1">{feature.title}</h4>
                      <p className="text-slate-500 text-sm">{feature.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <footer className="bg-slate-50 py-12 border-t border-blue-100 mt-auto">
        <div className="container mx-auto px-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-700 rounded-lg flex items-center justify-center text-white">
                <Activity className="w-4 h-4" />
              </div>
              <span className="text-xl font-bold text-slate-900">ITS.Core</span>
            </div>
            
            <div className="text-sm text-center md:text-right text-blue-600">
              <p className="mb-1 font-medium">{t('landing.footer.subtitle')}</p>
              <p className="flex items-center justify-center md:justify-end gap-1 text-blue-400">
                <MapPin className="w-4 h-4" /> {t('landing.footer.project')}
              </p>
            </div>
          </div>

          <div className="mt-6 text-center text-sm text-blue-400">
            {t('landing.footer.copyright')}
          </div>
        </div>
      </footer>

    </div>
  );
};

function ScanLineIcon(props: any) {
  return (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 7V5a2 2 0 0 1 2-2h2" />
      <path d="M17 3h2a2 2 0 0 1 2 2v2" />
      <path d="M21 17v2a2 2 0 0 1-2 2h-2" />
      <path d="M7 21H5a2 2 0 0 1-2-2v-2" />
      <line x1="7" x2="17" y1="12" y2="12" />
    </svg>
  )
}

export default LandingPage;