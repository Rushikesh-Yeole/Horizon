import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useQuery } from '@tanstack/react-query';
import { User } from 'lucide-react';
import { clsx } from 'clsx';

export default function NavBar() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { isAuthenticated, logout, login } = useAuth();
  const [isDemoLoading, setIsDemoLoading] = useState(false);
  
  const [credits, setCredits] = useState(null);
  const [exhausted, setExhausted] = useState(false);
  const [showDemoWelcome, setShowDemoWelcome] = useState(false);

  useEffect(() => {
    if (isAuthenticated && localStorage.getItem('demo_session_id')) {
      setCredits(Number(localStorage.getItem('demo_credits') || 100));
      if (localStorage.getItem('show_demo_welcome') === 'true') {
        setShowDemoWelcome(true);
      }
    } else {
      setCredits(null);
      setShowDemoWelcome(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    const handleMeterUpdate = (e) => {
      const remaining = Number(e.detail.remaining);
      setCredits(remaining);
      localStorage.setItem('demo_credits', remaining);
    };
    
    const handleMeterExhausted = () => {
      setExhausted(true);
    };

    window.addEventListener('meter-update', handleMeterUpdate);
    window.addEventListener('meter-exhausted', handleMeterExhausted);
    return () => {
      window.removeEventListener('meter-update', handleMeterUpdate);
      window.removeEventListener('meter-exhausted', handleMeterExhausted);
    };
  }, []);

  const { data: user } = useQuery({
    queryKey: ['user', 'me'],
    queryFn: async () => {
      const res = await api.get('/users/me');
      return res.data;
    },
    enabled: isAuthenticated
  });

  const handleDemoLogin = async () => {
    setIsDemoLoading(true);
    try {
      const res = await api.post('/auth/login', { email: 'demo@horizon.com', password: 'demo123' });
      login(res.data.access_token, res.data.email);
      setShowDemoWelcome(true);
      navigate('/discover');
    } catch (err) {
      console.error(err);
    } finally {
      setIsDemoLoading(false);
    }
  };

  const handleCloseWelcome = () => {
    setShowDemoWelcome(false);
    localStorage.removeItem('show_demo_welcome');
  };

  if (pathname === '/ingest' && !isAuthenticated) return null;

  return (
    <>
      <nav className="fixed top-0 w-full z-50 bg-white/75 backdrop-blur-xl border-b border-neutral-200/70 shadow-2xs transition-all">
        <div className="max-w-[1680px] w-full mx-auto px-4 sm:px-8 lg:px-12 xl:px-16 h-16 flex items-center justify-between gap-2">
          <Link to="/" className="font-extrabold tracking-tight text-lg sm:text-xl text-neutral-950 shrink-0">
            Horizon
          </Link>
          
          <div className="flex items-center gap-2 sm:gap-5 shrink-0">
            {credits !== null && (
              <div className="group relative flex items-center">
                {/* Minimal High-Signal Meter Pill */}
                <div className="flex items-center gap-1.5 sm:gap-2.5 px-2.5 sm:px-3.5 py-1.5 rounded-full border border-neutral-200 bg-neutral-50/90 hover:border-neutral-900 hover:bg-white transition-all cursor-pointer">
                  <span className={`w-2 h-2 rounded-full shrink-0 ${credits > 50 ? 'bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.5)] animate-pulse' : credits > 20 ? 'bg-amber-400' : 'bg-rose-500 animate-ping'}`} />
                  <span className="text-[11px] sm:text-xs font-mono font-semibold text-neutral-900 tabular-nums whitespace-nowrap">
                    {Math.round(credits)} <span className="text-neutral-400 font-normal hidden xs:inline">/ 100</span>
                  </span>
                </div>

                {/* Subtractive Developer Audit Popover */}
                <div className="absolute top-full right-0 mt-2 w-56 p-3 bg-neutral-950 text-white rounded-xl shadow-xl border border-neutral-800 opacity-0 group-hover:opacity-100 pointer-events-none group-hover:pointer-events-auto transition-all duration-150 translate-y-1 group-hover:translate-y-0 z-50">
                  <div className="flex justify-between items-center text-[10px] font-mono font-bold text-neutral-400 border-b border-neutral-800 pb-1.5 mb-2">
                    <span>COMPUTE METER</span>
                    <span className="text-emerald-400">ACTIVE</span>
                  </div>
                  <div className="space-y-1.5 text-xs font-mono">
                    <div className="flex justify-between text-neutral-400">
                      <span>Engine:</span>
                      <span className="text-neutral-200">Gemini 2.5</span>
                    </div>
                    <div className="flex justify-between text-neutral-400">
                      <span>Audit:</span>
                      <span className="text-neutral-200">ops.log_llm_cost</span>
                    </div>
                    <div className="flex justify-between text-neutral-400">
                      <span>Balance:</span>
                      <span className="text-white font-semibold">{credits.toFixed(1)} Units</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          
            {isAuthenticated ? (
              <div className="flex items-center gap-2 sm:gap-5">
                <Link to="/discover" className="text-xs sm:text-sm font-semibold text-neutral-700 hover:text-neutral-950 transition-colors">
                  Discover
                </Link>
                <Link to="/tree" className="text-xs sm:text-sm font-semibold text-neutral-700 hover:text-neutral-950 transition-colors">
                  <span className="hidden sm:inline">Career </span>Tree
                </Link>
                <button onClick={logout} className="text-xs sm:text-sm font-semibold text-neutral-500 hover:text-neutral-950 transition-colors hidden sm:block">
                  Disconnect
                </button>
                {/* Profile Circular Button */}
                <button
                  onClick={() => navigate('/profile')}
                  title="Profile & Settings"
                  className={clsx(
                    "w-8 h-8 sm:w-9 sm:h-9 rounded-full flex items-center justify-center border transition-all overflow-hidden select-none shrink-0",
                    pathname === '/profile'
                      ? "border-neutral-950 ring-2 ring-neutral-950/20 shadow-2xs bg-neutral-950 text-white"
                      : "border-neutral-300 bg-neutral-100 hover:border-neutral-950 hover:bg-neutral-200/80 text-neutral-800"
                  )}
                >
                  {user && user.user?.avatar_url ? (
                    <img 
                      src={`${api.defaults.baseURL}${user.user.avatar_url}`} 
                      alt="Profile Avatar" 
                      className="w-full h-full object-cover rounded-full"
                    />
                  ) : (
                    <User size={16} className="stroke-[2.2]" />
                  )}
                </button>
              </div>
            ) : (
               <div className="flex items-center gap-2 sm:gap-3">
                 <button 
                   onClick={handleDemoLogin} 
                   disabled={isDemoLoading} 
                   className="text-xs sm:text-sm font-semibold px-3 sm:px-4 py-1.5 sm:py-2 rounded-full border border-neutral-300 text-neutral-800 hover:border-neutral-950 hover:bg-neutral-50 transition-all disabled:opacity-50 whitespace-nowrap"
                 >
                   {isDemoLoading ? 'Loading...' : 'Try Demo'}
                 </button>
                 <Link 
                   to="/login" 
                   className="text-xs sm:text-sm font-semibold px-4 sm:px-5 py-1.5 sm:py-2 rounded-full bg-neutral-950 text-white hover:bg-neutral-800 transition-all shadow-sm whitespace-nowrap"
                 >
                   Login
                 </Link>
               </div>
            )}
          </div>
        </div>
      </nav>

      {/* Demo Started Welcome Modal */}
      {showDemoWelcome && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-neutral-950/60 backdrop-blur-md px-4 py-6 overflow-y-auto">
          <div className="bg-white rounded-3xl p-6 sm:p-8 max-w-lg w-full shadow-2xl border border-neutral-200/80 animate-in fade-in zoom-in-95 duration-200 text-left relative overflow-hidden my-auto max-h-[90vh] overflow-y-auto">
            {/* Top Accent Light */}
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 via-teal-400 to-indigo-500" />
            
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2.5">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-xs font-mono font-bold tracking-wider uppercase text-neutral-500">
                  Demo Session Initialized
                </span>
              </div>
              <span className="text-xs font-mono font-bold px-2.5 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200/80 rounded-md">
                100 Compute Credits
              </span>
            </div>

            <h2 className="text-2xl font-extrabold tracking-tight text-neutral-950 mb-2">
              Demo Started
            </h2>
            <p className="text-sm text-neutral-600 leading-relaxed mb-6">
              Signed in as <strong className="text-neutral-900 font-semibold">Alex Chen</strong> (AI Research Engineer). Your profile is pre-seeded for immediate graph evaluation.
            </p>

            {/* Modules Showcase */}
            <div className="space-y-3 mb-8">
              <div className="p-3.5 rounded-2xl bg-neutral-50 border border-neutral-200/70 flex items-start gap-3">
                <div className="w-8 h-8 rounded-xl bg-neutral-950 text-white flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">
                  01
                </div>
                <div>
                  <h4 className="text-sm font-bold text-neutral-950">Discovery Engine</h4>
                  <p className="text-xs text-neutral-600 leading-snug">Run live Greenhouse/Lever JD audits & score target company stack fit.</p>
                </div>
              </div>

              <div className="p-3.5 rounded-2xl bg-neutral-50 border border-neutral-200/70 flex items-start gap-3">
                <div className="w-8 h-8 rounded-xl bg-neutral-950 text-white flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">
                  02
                </div>
                <div>
                  <h4 className="text-sm font-bold text-neutral-950">Career Trajectory Tree</h4>
                  <p className="text-xs text-neutral-600 leading-snug">Synthesize 5-path roadmaps triangulated across verified web evidence.</p>
                </div>
              </div>

              <div className="p-3.5 rounded-2xl bg-neutral-50 border border-neutral-200/70 flex items-start gap-3">
                <div className="w-8 h-8 rounded-xl bg-neutral-950 text-white flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">
                  03
                </div>
                <div>
                  <h4 className="text-sm font-bold text-neutral-950">Profile Configuration</h4>
                  <p className="text-xs text-neutral-600 leading-snug">Configure your skills, target role, & location in Profile to test graph adaptation.</p>
                </div>
              </div>
            </div>

            {/* Action Footer */}
            <div className="flex items-center justify-between pt-2">
              <span className="text-xs text-neutral-500 font-mono">
                Metered in top navigation bar
              </span>
              <button
                onClick={handleCloseWelcome}
                className="px-6 py-2.5 rounded-full bg-neutral-950 text-white text-sm font-semibold hover:bg-neutral-800 transition-all shadow-sm"
              >
                Explore Sandbox &rarr;
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Exhausted Quota Modal */}
      {exhausted && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-neutral-950/60 backdrop-blur-md">
          <div className="bg-white p-8 rounded-2xl shadow-2xl max-w-sm w-full mx-4 border border-neutral-200 animate-in fade-in zoom-in-95 duration-200">
            <div className="w-10 h-10 rounded-xl bg-rose-100 text-rose-600 flex items-center justify-center font-bold text-lg mb-4">!</div>
            <h3 className="text-xl font-bold text-neutral-950 mb-2">LLM Quota Exhausted</h3>
            <p className="text-neutral-600 text-sm leading-relaxed mb-6">
              You have used all demo compute credits. Log in or create a full account to continue running the career graph engine.
            </p>
            <button 
              onClick={() => {
                logout();
                setExhausted(false);
              }}
              className="w-full py-3 bg-neutral-950 text-white rounded-full font-semibold text-sm hover:bg-neutral-800 transition-colors shadow-sm"
            >
              Log In / Sign Up
            </button>
          </div>
        </div>
      )}
    </>
  );
}
