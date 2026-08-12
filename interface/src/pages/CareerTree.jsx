import { useState } from 'react';
import api from '../services/api';
import { toast } from 'sonner';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../context/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  GitBranch, ExternalLink, Clock, Target, 
  ChevronDown, AlertCircle, Loader2, Sparkles, 
  BookOpen, Link as LinkIcon, RefreshCw 
} from 'lucide-react';
import { clsx } from 'clsx';

const StageCard = ({ stage, index, isLast }) => {
  const getDomain = (url) => {
    try { return new URL(url).hostname.replace('www.', ''); } catch { return ''; }
  };

  return (
    <div className="relative pl-8 pb-10 last:pb-0">
      {!isLast && <div className="absolute left-[11px] top-3 bottom-0 w-px bg-gray-200/80"></div>}
      <div className="absolute left-0 top-1.5 w-[22px] h-[22px] bg-white border-2 border-gray-200 rounded-full flex items-center justify-center z-10 shadow-sm">
        <div className="w-1.5 h-1.5 bg-black rounded-full"></div>
      </div>
      <div className="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm hover:shadow-md transition-all duration-300 group">
        <div className="mb-3">
          <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-1 flex items-center">
            Checkpoint {index + 1} <span className="mx-2">•</span> {stage.eta_months} Months
          </span>
          <h4 className="text-lg font-bold text-gray-900 group-hover:text-black transition-colors">
            {stage.name}
          </h4>
        </div>
        <p className="text-sm text-gray-600 leading-relaxed mb-4 whitespace-pre-line border-l-2 border-gray-100 pl-3">
          {stage.description}
        </p>
        <div className="bg-gray-50/50 rounded-xl p-3 border border-gray-100 space-y-3">
          {stage.citations?.length > 0 && (
            <div className="flex items-start gap-3">
              <div className="mt-0.5 min-w-max p-1.5 bg-purple-50 text-purple-600 rounded-lg">
                <BookOpen size={14} />
              </div>
              <div className="w-full">
                <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wide block mb-1.5">
                  Verified Biographies
                </span>
                <div className="flex flex-wrap gap-2">
                  {[...new Set(stage.citations)].map((url, i) => (
                    <a key={i} href={url} target="_blank" rel="noreferrer" 
                       className="inline-flex items-center gap-1.5 px-2 py-1 bg-white border border-gray-200 rounded-md text-[10px] font-medium text-gray-600 hover:text-purple-600 hover:border-purple-200 transition-colors">
                      <LinkIcon size={10} /> {getDomain(url)}
                    </a>
                  ))}
                </div>
              </div>
            </div>
          )}
          {stage.top_opportunities?.length > 0 && stage.top_opportunities[0].url && (
            <div className="flex items-start gap-3 pt-2 border-t border-gray-200/50">
              <div className="mt-0.5 min-w-max p-1.5 bg-blue-50 text-blue-600 rounded-lg">
                <Target size={14} />
              </div>
              <div>
                <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wide block">Actionables</span>
                <a href={stage.top_opportunities[0].url} target="_blank" rel="noreferrer"
                   className="block text-sm font-semibold text-gray-900 leading-tight mt-0.5 hover:text-blue-600 hover:underline">
                  {stage.top_opportunities[0].title}
                </a>
                <p className="text-xs text-gray-500 mt-0.5 block line-clamp-2">
                  {stage.top_opportunities[0].snippet}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default function CareerTree() {
  const { token } = useAuth();
  const [selectedPathIndex, setSelectedPathIndex] = useState(0);
  const [mobileExpandedPath, setMobileExpandedPath] = useState(0);

  const { data: tree, isLoading: loading, error, refetch } = useQuery({
    queryKey: ['careerTree'],
    queryFn: async () => {
      const res = await api.get('/career/tree');
      return res.data;
    },
    enabled: !!token
  });

  if (error) {
    toast.error("The Biographer Engine is recalibrating. Please try again.");
  }

  if (loading && !tree) return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-white">
      <Loader2 className="w-8 h-8 animate-spin text-neutral-950 mb-3" />
      <span className="text-xs font-mono text-neutral-500">Researching Career Advisory Evidence...</span>
    </div>
  );

  const activePath = tree?.paths?.[selectedPathIndex] || tree?.paths?.[0];

  return (
    <div className="min-h-screen bg-white pt-24 sm:pt-28 pb-20 px-4 sm:px-8 lg:px-12 xl:px-16 max-w-[1680px] w-full mx-auto">
      
      {/* Header */}
      <div className="max-w-3xl mx-auto text-center mb-10 sm:mb-12 animate-fade-in relative">
        <div className="inline-flex items-center justify-center px-4 py-1.5 bg-neutral-50 rounded-full shadow-2xs border border-neutral-200 mb-4 sm:mb-5">
          <BookOpen className="w-3.5 h-3.5 mr-2 text-indigo-600" />
          <span className="text-[10px] font-mono font-bold uppercase tracking-widest text-neutral-600">Evidence-Based Roadmap</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-neutral-950 mb-3 sm:mb-4">The Serendipity Engine</h1>
        <p className="text-sm sm:text-base text-neutral-600 mb-6 leading-relaxed">
          Analyzed 42+ real-world trajectories & market evidence.<br />
          Synthesized <span className="text-neutral-950 font-semibold">3 Personalized Career Paths</span>.
        </p>
        
        <button 
          onClick={() => refetch()}
          disabled={loading}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-white border border-neutral-200 rounded-full text-xs font-bold text-neutral-800 hover:border-neutral-950 hover:bg-neutral-50 transition-all shadow-2xs active:scale-95 disabled:opacity-50 cursor-pointer"
        >
          <RefreshCw size={14} className={clsx(loading && "animate-spin")} />
          {loading ? "Doing Deep research..." : "Recalibrate Trajectories"}
        </button>
      </div>

      {error && (
        <div className="max-w-md mx-auto mb-10 bg-white p-6 rounded-2xl shadow-sm border border-rose-100 flex flex-col items-center text-center">
          <AlertCircle className="w-8 h-8 text-rose-500 mb-3" />
          <p className="text-neutral-600 text-sm mb-4">The Biographer Engine is recalibrating. Please try again.</p>
          <button onClick={() => refetch()} className="px-5 py-2 bg-neutral-950 text-white rounded-full text-xs font-bold">Retry</button>
        </div>
      )}

      {/* 1. LAPTOP DUAL-PANE VIEW (Visible on lg/xl screens) */}
      <div className="hidden lg:grid lg:grid-cols-12 gap-8 items-start">
        
        {/* Left Column: Trajectory Switcher Sidebar */}
        <div className="lg:col-span-4 space-y-4 sticky top-24">
          <div className="flex items-center justify-between pb-2 border-b border-neutral-200">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-neutral-500">Synthesized Trajectories</span>
            <span className="text-xs font-mono text-neutral-400">3 Paths</span>
          </div>

          <div className="space-y-3">
            {tree?.paths?.map((path, idx) => {
              const isSelected = selectedPathIndex === idx;
              const isBestFit = idx === 0;

              return (
                <div
                  key={path.id || idx}
                  onClick={() => setSelectedPathIndex(idx)}
                  className={clsx(
                    "p-5 rounded-2xl border transition-all duration-200 cursor-pointer text-left relative",
                    isSelected
                      ? "bg-neutral-950 text-white border-neutral-950 shadow-md ring-2 ring-neutral-950/10"
                      : "bg-white text-neutral-900 border-neutral-200/80 hover:border-neutral-400 hover:bg-neutral-50/50 shadow-2xs"
                  )}
                >
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div className="flex items-center gap-2.5">
                      <span className={clsx(
                        "w-6 h-6 rounded-md flex items-center justify-center text-xs font-mono font-bold shrink-0",
                        isSelected ? "bg-white text-neutral-950" : "bg-neutral-100 text-neutral-800"
                      )}>
                        {idx + 1}
                      </span>
                      <h3 className={clsx("font-bold text-sm leading-snug", isSelected ? "text-white" : "text-neutral-950")}>
                        {path.title}
                      </h3>
                    </div>
                  </div>

                  <p className={clsx("text-xs line-clamp-2 mb-3 leading-relaxed", isSelected ? "text-neutral-300" : "text-neutral-600")}>
                    {path.summary}
                  </p>

                  <div className="flex items-center justify-between pt-2 border-t border-neutral-200/30 text-xs font-mono">
                    <div className="flex items-center gap-3">
                      <span className={clsx("flex items-center font-semibold", isSelected ? "text-emerald-400" : "text-emerald-600")}>
                        <Target size={12} className="mr-1" /> {(path.fit_score).toFixed(0)}% Match
                      </span>
                      <span className={clsx("flex items-center", isSelected ? "text-neutral-400" : "text-neutral-500")}>
                        <Clock size={12} className="mr-1" /> ~{path.stages?.reduce((a, c) => a + c.eta_months, 0)} Mo
                      </span>
                    </div>
                    {isBestFit && (
                      <span className={clsx(
                        "px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider flex items-center shrink-0",
                        isSelected ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30" : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                      )}>
                        Top Match
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* System Verification Capsule */}
          <div className="p-4 rounded-2xl bg-neutral-50 border border-neutral-200/80 text-xs font-mono text-neutral-600 space-y-1.5">
            <div className="flex justify-between items-center text-[10px] font-bold uppercase text-neutral-400">
              <span>Graph Intelligence</span>
              <span className="text-emerald-600">Deterministic</span>
            </div>
            <div className="flex justify-between text-neutral-700">
              <span>Verified Biographies:</span>
              <span className="font-semibold text-neutral-950">42 Profiles</span>
            </div>
            <div className="flex justify-between text-neutral-700">
              <span>Graph Hop Depth:</span>
              <span className="font-semibold text-neutral-950">15-Hop Neo4j</span>
            </div>
          </div>
        </div>

        {/* Right Column: Active Trajectory Detail Timeline */}
        <div className="lg:col-span-8 space-y-6">
          {activePath && (
            <div className="animate-fade-in space-y-6">
              {/* Strategic Intent Hero Card */}
              <div className="bg-neutral-50/70 p-6 sm:p-7 rounded-3xl border border-neutral-200/80 shadow-2xs">
                <div className="flex items-center justify-between gap-4 mb-3">
                  <div className="flex items-center gap-3">
                    <span className="px-2.5 py-1 rounded-lg bg-neutral-950 text-white font-mono text-xs font-bold">
                      Path 0{selectedPathIndex + 1}
                    </span>
                    <h2 className="text-xl sm:text-2xl font-extrabold text-neutral-950 tracking-tight">
                      {activePath.title}
                    </h2>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs font-mono font-bold px-3 py-1 bg-white border border-neutral-200 rounded-full text-neutral-800 shadow-2xs">
                      {(activePath.fit_score).toFixed(0)}% Profile Fit
                    </span>
                  </div>
                </div>

                <p className="text-sm text-neutral-700 leading-relaxed pt-2 border-t border-neutral-200/60">
                  {activePath.summary}
                </p>
              </div>

              {/* Sequential Checkpoint Timeline */}
              <div className="bg-white p-6 sm:p-8 rounded-3xl border border-neutral-200/80 shadow-2xs">
                <div className="mb-6 pb-3 border-b border-neutral-100 flex items-center justify-between">
                  <span className="text-xs font-mono font-bold uppercase tracking-wider text-neutral-500">
                    Sequential Execution Path ({activePath.stages?.length || 0} Checkpoints)
                  </span>
                  <span className="text-xs font-mono text-neutral-400">
                    Est. {activePath.stages?.reduce((a, c) => a + c.eta_months, 0)} Months Total
                  </span>
                </div>

                <div className="pl-2">
                  {activePath.stages?.map((stage, sIdx) => (
                    <StageCard key={sIdx} stage={stage} index={sIdx} isLast={sIdx === activePath.stages.length - 1} />
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

      </div>

      {/* 2. MOBILE ACCORDION VIEW (Visible on mobile/tablet screens < lg) */}
      <div className="block lg:hidden space-y-4">
        {tree?.paths?.map((path, idx) => {
          const isExpanded = mobileExpandedPath === idx;
          const isBestFit = idx === 0;

          return (
            <motion.div 
              key={path.id || idx}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              className={clsx(
                "bg-white rounded-2xl overflow-hidden border transition-all duration-300",
                isExpanded ? "shadow-xl shadow-black/5 border-neutral-300 ring-1 ring-neutral-950/5" : "shadow-2xs border-neutral-200/80 hover:border-neutral-400 cursor-pointer"
              )}
            >
              <div onClick={() => setMobileExpandedPath(isExpanded ? null : idx)} className="p-4 sm:p-6 flex items-center justify-between gap-3">
                <div className="flex items-center gap-3 sm:gap-5 min-w-0">
                  <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl flex items-center justify-center text-base sm:text-lg font-bold shrink-0 shadow-inner bg-neutral-950 text-white">
                    {idx + 1}
                  </div>
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <h3 className="text-base sm:text-lg font-bold text-neutral-950 truncate">{path.title}</h3>
                      {isBestFit && (
                        <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-emerald-50 text-emerald-700 uppercase border border-emerald-200 flex items-center shrink-0">
                          <Sparkles size={10} className="mr-1"/> Best Advice
                        </span>
                      )}
                    </div>
                    <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-xs font-mono text-neutral-500">
                      <span className="flex items-center"><Target size={12} className="mr-1 shrink-0" /> {(path.fit_score).toFixed(0)}% Match</span>
                      <span className="flex items-center"><Clock size={12} className="mr-1 shrink-0" /> ~{path.stages?.reduce((a, c) => a + c.eta_months, 0)} Mo</span>
                    </div>
                  </div>
                </div>
                <ChevronDown size={20} className={clsx("text-neutral-400 transition-transform duration-300 shrink-0", isExpanded && "rotate-180 text-neutral-950")} />
              </div>

              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <div className="px-4 sm:px-6 pb-6 pt-2 border-t border-neutral-100 bg-neutral-50/40">
                      <div className="mb-6 bg-white p-4 rounded-xl border border-neutral-200/80 shadow-2xs">
                        <span className="font-mono font-bold text-neutral-950 block mb-1 uppercase tracking-wider text-[10px]">Strategic Intent</span>
                        <p className="text-xs sm:text-sm text-neutral-700 leading-relaxed">{path.summary}</p>
                      </div>
                      <div className="pl-1">
                        {path.stages?.map((stage, sIdx) => (
                          <StageCard key={sIdx} stage={stage} index={sIdx} isLast={sIdx === path.stages.length - 1} />
                        ))}
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          );
        })}
      </div>

    </div>
  );
}