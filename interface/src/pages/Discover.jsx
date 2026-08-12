import { useState } from 'react';
import api from '../services/api';
import { toast } from 'sonner';
import { useAuth } from '../context/AuthContext';
import { Card, Button, Input } from '../components/UI';
import { Search, Zap, AlertTriangle, CheckCircle, Loader2, RefreshCw, Database, Globe } from 'lucide-react';

export default function Discover() {
  const { token } = useAuth();
  const [criteria, setCriteria] = useState({ 
    role: "Frontend Engineer", 
    location: "Bangalore", 
    companies: "Google" 
  });
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [refreshingCompany, setRefreshingCompany] = useState(null);

  const runSearch = async (forceRefresh = false, singleCompany = null) => {
    if (!token) {
      toast.error("Session expired. Please re-initialize.");
      return;
    }

    if (singleCompany) setRefreshingCompany(singleCompany);
    else setLoading(true);

    const targetCompanies = singleCompany 
      ? [singleCompany]
      : criteria.companies.split(",").map((c) => c.trim());

    try {
      const res = await api.post(
        `/discover/search${forceRefresh ? '?force_refresh=true' : ''}`,
        {
          search_criteria: {
            role: criteria.role,
            location: criteria.location,
            target_companies: targetCompanies,
          }
        }
      );
      const newCards = res.data.guidance_cards;
      if (singleCompany) {
        setResults(prev => prev.map(c => 
          c.company_name === singleCompany ? (newCards[0] || c) : c
        ));
        toast.success(`Refreshed ${singleCompany} with live data.`);
      } else {
        setResults(newCards);
      }
    } catch (err) {
      const errorMsg = err.response?.data?.detail || "Physics Engine Stalled. Backend unreachable.";
      toast.error(`System Failure: ${errorMsg}`);
    } finally {
      setLoading(false);
      setRefreshingCompany(null);
    }
  };

  const formatDate = (isoStr) => {
    if (!isoStr) return null;
    try {
      return new Date(isoStr).toLocaleDateString('en-US', { 
        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' 
      });
    } catch { return null; }
  };

  return (
    <div className="max-w-[1680px] w-full mx-auto pt-24 sm:pt-28 pb-20 px-4 sm:px-8 lg:px-12 xl:px-16 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-3 mb-8 sm:mb-10">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-neutral-950">Discovery Search</h1>
          <p className="text-sm text-neutral-600 font-normal mt-1">Multi-layer deterministic search for candidate-role fit.</p>
        </div>
      </div>

      {/* Input Control Panel */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-10 sm:mb-12">
        <div className="lg:col-span-1">
          <Input label="Target Role" value={criteria.role} onChange={e => setCriteria({...criteria, role: e.target.value})} />
        </div>
        <div className="lg:col-span-1">
          <Input label="Geography" value={criteria.location} onChange={e => setCriteria({...criteria, location: e.target.value})} />
        </div>
        <div className="lg:col-span-1">
          <Input label="Target Firms (multiple)" placeholder="Comma separated" value={criteria.companies} onChange={e => setCriteria({...criteria, companies: e.target.value})} />
        </div>
        <div className="lg:col-span-1 flex items-end">
          <Button onClick={() => runSearch(false)} isLoading={loading} className="w-full h-11 sm:h-12 shadow-sm">
            {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2 inline" /> : <Search className="w-4 h-4 mr-2 inline" />} 
            Search
          </Button>
        </div>
      </div>

      {/* Results */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 items-start">
        {results?.map((card, i) => (
          <Card key={i} className={`border-l-4 border-l-neutral-950 group ${results.length === 1 ? 'xl:col-span-2' : ''}`}>
            <div className="flex flex-col sm:flex-row justify-between items-start gap-4 mb-4">
              <div className="flex-1">
                <h2 className="text-xl sm:text-2xl font-bold capitalize tracking-tight text-neutral-950">{card.company_name}</h2>
                <div className="flex flex-wrap gap-2 items-center mt-1.5">
                  <span className="text-[10px] uppercase tracking-widest bg-neutral-100 px-2 py-0.5 rounded font-bold text-neutral-700">
                    {card.hiring_bar_difficulty} Bar
                  </span>
                  <span className="text-[10px] uppercase tracking-widest text-neutral-500 font-bold">
                    {card.feasibility_timeline_weeks} Weeks to bridge
                  </span>

                  {/* Cache status badge */}
                  {card.from_cache !== undefined && (
                    <span className={`inline-flex items-center gap-1 text-[10px] uppercase tracking-widest font-bold px-2 py-0.5 rounded ${
                      card.from_cache 
                        ? 'bg-amber-50 text-amber-700 border border-amber-200' 
                        : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    }`}>
                      {card.from_cache 
                        ? <><Database className="w-2.5 h-2.5" /> Cached</> 
                        : <><Globe className="w-2.5 h-2.5" /> Live</>}
                    </span>
                  )}

                  {/* Retrieved at */}
                  {card.retrieved_at && (
                    <span className="text-[10px] text-neutral-400 font-medium">
                      Retrieved {formatDate(card.retrieved_at)}
                    </span>
                  )}
                </div>
              </div>

              <div className="flex flex-col items-end gap-2 self-start shrink-0">
                <div className="text-right">
                  <div className="text-3xl sm:text-4xl font-extrabold tracking-tighter tabular-nums text-neutral-950">{card.fit_score}%</div>
                  <div className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest">Evidence Coverage</div>
                </div>
                {/* Re-run Research */}
                <button
                  onClick={() => runSearch(true, card.company_name)}
                  disabled={refreshingCompany === card.company_name}
                  title="Bypass cache — fetch live JD & intel"
                  className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest text-neutral-400 hover:text-neutral-900 transition-colors disabled:opacity-40 cursor-pointer"
                >
                  <RefreshCw className={`w-3 h-3 ${refreshingCompany === card.company_name ? 'animate-spin' : ''}`} />
                  {refreshingCompany === card.company_name ? 'Refreshing…' : 'Re-run Research'}
                </button>
              </div>
            </div>
            
            <p className="text-base sm:text-lg font-medium mb-6 text-neutral-800 leading-snug">"{card.verdict_headline}"</p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8">
              {/* Reasoning Trace */}
              <div className="bg-neutral-50 p-5 rounded-2xl border border-neutral-100">
                <h3 className="text-[11px] sm:text-[12px] font-bold uppercase text-neutral-500 mb-2.5 flex items-center tracking-widest">
                  <Zap className="w-3 h-3 mr-1.5 fill-neutral-950"/> Reasoning Trace
                </h3>
                <p className="text-xs sm:text-sm font-mono text-neutral-700 leading-relaxed italic">{card.reasoning_trace}</p>
                <h3 className="text-[11px] sm:text-[12px] font-bold uppercase text-neutral-500 mb-2.5 mt-5 flex items-center tracking-widest">
                  <Zap className="w-3 h-3 mr-1.5 fill-neutral-950"/> Advice
                </h3>
                <p className="text-xs sm:text-sm font-mono text-neutral-700 italic">{card.main_advisory_text}</p>
              </div>
              
              {/* Gap & Action Analysis */}
              <div>
                <h3 className="text-[11px] sm:text-[12px] font-bold uppercase text-neutral-500 mb-2.5 flex items-center tracking-widest">
                  <AlertTriangle className="w-3 h-3 mr-1.5"/> Skill Gaps
                </h3>
                <div className="flex flex-wrap gap-1.5 mb-6">
                  {card.user_skill_gaps?.length > 0 ? card.user_skill_gaps.map(gap => (
                    <span key={gap} className="px-2.5 py-1 bg-rose-50 text-rose-700 text-[11px] font-bold rounded-md border border-rose-200 uppercase tracking-tight">
                      {gap}
                    </span>
                  )) : <span className="text-emerald-600 text-xs font-semibold">Paradigm alignment verified.</span>}
                </div>

                <h3 className="text-[11px] sm:text-[12px] font-bold uppercase text-neutral-500 mb-2.5 flex items-center tracking-widest">
                  <CheckCircle className="w-3 h-3 mr-1.5"/> Execution Path
                </h3>
                <ul className="space-y-2.5">
                  {card.actionable_path?.map((step, idx) => (
                    <li key={idx} className="text-xs sm:text-sm text-neutral-800 flex items-start leading-snug">
                      <span className="mr-2.5 font-mono text-neutral-400 font-bold shrink-0">{idx+1}.</span> 
                      <span>{step}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </Card>
        ))}
        
        {/* Empty State */}
        {!results && !loading && (
          <div className="col-span-full py-20 text-center border-2 border-dashed border-neutral-200 rounded-3xl">
            <p className="text-neutral-400 font-medium font-mono text-sm">Input parameters to query the Search Engine.</p>
          </div>
        )}
      </div>
    </div>
  );
}