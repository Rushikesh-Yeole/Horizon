import { useState } from 'react';
import api from '../services/api';
import { toast } from 'sonner';
import { useAuth } from '../context/AuthContext';
import { Card, Button, Input } from '../components/UI';
import { Search, Zap, AlertTriangle, CheckCircle, Loader2, RefreshCw, Database, Globe } from 'lucide-react';

export default function Discover() {
  const { token } = useAuth();
  const [criteria, setCriteria] = useState({
    role: "AI Systems Engineer",
    location: "San Francisco",
    companies: "OpenAI, Anthropic, Meta"
  });
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [refreshingCompany, setRefreshingCompany] = useState(null);

  const presets = [
    { role: "AI Systems Engineer", location: "San Francisco", companies: "OpenAI, Anthropic, Meta", label: "Frontier AI Labs" },
    { role: "AI Infrastructure Engineer", location: "New York", companies: "Databricks, Scale AI, Stripe", label: "AI Infra & Scale" },
    { role: "Staff Research Engineer", location: "London", companies: "Google DeepMind, Mistral AI", label: "Frontier Research" },
  ];

  const applyPreset = (p) => {
    setCriteria({ role: p.role, location: p.location, companies: p.companies });
  };

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
          <p className="text-sm sm:text-base text-neutral-700 font-medium mt-1">Multi-layer evidence-backed search for candidate-role fit.</p>
        </div>
      </div>

      {/* Input Control Panel */}
      <div className="mb-10 sm:mb-12">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-3.5">
          <div className="lg:col-span-1">
            <Input label="Target Role" value={criteria.role} onChange={e => setCriteria({ ...criteria, role: e.target.value })} />
          </div>
          <div className="lg:col-span-1">
            <Input label="Geography" value={criteria.location} onChange={e => setCriteria({ ...criteria, location: e.target.value })} />
          </div>
          <div className="lg:col-span-1">
            <Input label="Target Firms (Comma Separated)" placeholder="Comma separated" value={criteria.companies} onChange={e => setCriteria({ ...criteria, companies: e.target.value })} />
          </div>
          <div className="lg:col-span-1 flex items-end">
            <Button onClick={() => runSearch(false)} isLoading={loading} className="w-full h-11 sm:h-12 shadow-sm font-bold text-sm sm:text-base">
              {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2 inline" /> : <Search className="w-4 h-4 mr-2 inline" />}
              Search
            </Button>
          </div>
        </div>

        {/* Frontier Presets */}
        <div className="flex flex-wrap items-center gap-2 pt-1.5">
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-neutral-700 mr-1">
            AI Presets:
          </span>
          {presets.map((p, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => applyPreset(p)}
              className="text-xs font-mono font-bold px-3.5 py-1.5 rounded-full bg-neutral-100 hover:bg-neutral-950 hover:text-white text-neutral-800 transition-all border border-neutral-300 shadow-2xs cursor-pointer flex items-center gap-1.5"
            >
              <span>{p.label}</span>
              <span className="text-[11px] text-neutral-500 font-semibold">({p.role.split(' ')[0]})</span>
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      <div className="flex flex-col gap-8 w-full">
        {results?.map((card, i) => (
          <Card key={i} className="w-full border-l-4 border-l-neutral-950 p-6 sm:p-8 rounded-3xl shadow-sm hover:shadow-md transition-shadow">
            {/* Top Bar: Company Meta + Fit Score */}
            <div className="flex flex-col sm:flex-row justify-between items-start gap-4 mb-6 pb-5 border-b border-neutral-100">
              <div className="flex-1">
                <h2 className="text-2xl sm:text-3xl font-extrabold capitalize tracking-tight text-neutral-950">{card.company_name}</h2>
                <div className="flex flex-wrap gap-2.5 items-center mt-2.5">
                  <span className="text-xs uppercase tracking-wider bg-neutral-100 px-3 py-1 rounded-md font-bold text-neutral-900 border border-neutral-200">
                    {card.hiring_bar_difficulty} Bar
                  </span>
                  <span className="text-xs uppercase tracking-wider text-neutral-800 font-bold bg-neutral-50 px-3 py-1 rounded-md border border-neutral-200">
                    {card.feasibility_timeline_weeks} Weeks to bridge
                  </span>

                  {/* Cache status badge */}
                  {card.from_cache !== undefined && (
                    <span className={`inline-flex items-center gap-1.5 text-xs uppercase tracking-wider font-bold px-3 py-1 rounded-md ${card.from_cache
                      ? 'bg-amber-50 text-amber-900 border border-amber-200'
                      : 'bg-emerald-50 text-emerald-900 border border-emerald-200'
                      }`}>
                      {card.from_cache
                        ? <><Database className="w-3.5 h-3.5" /> Cached</>
                        : <><Globe className="w-3.5 h-3.5" /> Live JD Fetch</>}
                    </span>
                  )}

                  {/* Retrieved at */}
                  {card.retrieved_at && (
                    <span className="text-xs text-neutral-500 font-mono font-medium">
                      Retrieved {formatDate(card.retrieved_at)}
                    </span>
                  )}
                </div>
              </div>

              <div className="flex flex-col items-start sm:items-end gap-2 self-start shrink-0">
                <div className="text-left sm:text-right">
                  <div className="text-3xl sm:text-4xl font-extrabold tracking-tighter tabular-nums text-neutral-950">{card.fit_score}%</div>
                  <div className="text-[11px] font-bold text-neutral-600 uppercase tracking-wider font-mono">Evidence Coverage</div>
                </div>
                {/* Re-run Search */}
                <button
                  onClick={() => runSearch(true, card.company_name)}
                  disabled={refreshingCompany === card.company_name}
                  title="Bypass cache — fetch live JD & intel"
                  className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-neutral-600 hover:text-neutral-950 transition-colors disabled:opacity-40 cursor-pointer pt-1"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${refreshingCompany === card.company_name ? 'animate-spin' : ''}`} />
                  {refreshingCompany === card.company_name ? 'Refreshing…' : 'Re-run Live Search'}
                </button>
              </div>
            </div>

            {/* Headline Verdict */}
            <div className="mb-6 p-4 sm:p-5 rounded-2xl bg-neutral-50 border border-neutral-200/80">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-neutral-600 block mb-1.5">
                Agnostic Semantic Verdict
              </span>
              <p className="text-lg sm:text-xl font-bold text-neutral-950 leading-snug">"{card.verdict_headline}"</p>
            </div>

            {/* Horizontal Split Details: Reasoning + Gaps & Execution */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 sm:gap-8 items-start">
              {/* Reasoning Trace & Advisory (6 Cols on large) */}
              <div className="lg:col-span-6 space-y-4 bg-neutral-50/60 p-5 sm:p-6 rounded-2xl border border-neutral-100">
                <div>
                  <h3 className="text-xs sm:text-sm font-bold uppercase text-neutral-800 mb-2 flex items-center tracking-wider font-mono">
                    <Zap className="w-3.5 h-3.5 mr-1.5 text-amber-600 fill-amber-600" /> Reasoning Trace
                  </h3>
                  <p className="text-xs sm:text-sm font-mono text-neutral-900 leading-relaxed bg-white p-4 rounded-xl border border-neutral-200/70">
                    {card.reasoning_trace}
                  </p>
                </div>

                <div>
                  <h3 className="text-xs sm:text-sm font-bold uppercase text-neutral-800 mb-2 flex items-center tracking-wider font-mono">
                    <Zap className="w-3.5 h-3.5 mr-1.5 text-amber-600 fill-amber-600" /> Core Advisory
                  </h3>
                  <p className="text-xs sm:text-sm font-mono text-neutral-950 bg-white p-4 rounded-xl border border-neutral-200/70 font-semibold leading-relaxed">
                    {card.main_advisory_text}
                  </p>
                </div>
              </div>

              {/* Gap & Action Analysis (6 Cols on large) */}
              <div className="lg:col-span-6 space-y-5">
                <div>
                  <h3 className="text-xs sm:text-sm font-bold uppercase text-neutral-800 mb-2.5 flex items-center tracking-wider font-mono">
                    <AlertTriangle className="w-3.5 h-3.5 mr-1.5 text-rose-600" /> Strictly Absent Skill Gaps
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {card.user_skill_gaps?.length > 0 ? card.user_skill_gaps.map(gap => (
                      <span key={gap} className="px-3.5 py-1.5 bg-rose-50 text-rose-800 text-xs sm:text-sm font-bold rounded-lg border border-rose-200 font-mono uppercase tracking-tight">
                        {gap}
                      </span>
                    )) : (
                      <span className="text-emerald-800 bg-emerald-50 px-3.5 py-1.5 rounded-lg border border-emerald-200 text-xs sm:text-sm font-bold font-mono">
                        ✓ Full stack paradigm alignment verified
                      </span>
                    )}
                  </div>
                </div>

                <div>
                  <h3 className="text-xs sm:text-sm font-bold uppercase text-neutral-800 mb-2.5 flex items-center tracking-wider font-mono">
                    <CheckCircle className="w-3.5 h-3.5 mr-1.5 text-emerald-600" /> Actionable Execution Path
                  </h3>
                  <ul className="space-y-2.5">
                    {card.actionable_path?.map((step, idx) => (
                      <li key={idx} className="text-xs sm:text-sm text-neutral-900 flex items-start leading-snug bg-neutral-50/80 p-3.5 rounded-xl border border-neutral-200/60">
                        <span className="mr-3 font-mono text-neutral-800 font-extrabold shrink-0 bg-white w-6 h-6 rounded-full flex items-center justify-center border border-neutral-300 text-xs shadow-2xs">
                          {idx + 1}
                        </span>
                        <span className="font-semibold text-neutral-950 mt-0.5">{step}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </Card>
        ))}

        {/* Empty State */}
        {!results && !loading && (
          <div className="w-full py-20 text-center border-2 border-dashed border-neutral-200 rounded-3xl bg-neutral-50/40">
            <p className="text-neutral-700 font-semibold font-mono text-sm sm:text-base">Input target parameters to query the Discover Engine.</p>
          </div>
        )}
      </div>
    </div>
  );
}