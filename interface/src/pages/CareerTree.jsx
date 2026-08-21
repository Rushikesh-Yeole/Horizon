import { useState } from 'react';
import api from '../services/api';
import { toast } from 'sonner';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../context/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import {
  GitBranch, ExternalLink, Clock, Target,
  ChevronDown, AlertCircle, Loader2, Sparkles,
  BookOpen, Link as LinkIcon, RefreshCw
} from 'lucide-react';
import { clsx } from 'clsx';

const formatDurationYears = (months, compact = false) => {
  const yrs = (Number(months || 0) / 12).toFixed(1);
  if (compact) {
    return `${yrs} Yrs`;
  }
  return `${yrs} ${yrs === '1.0' ? 'Year' : 'Years'}`;
};

const StageCard = ({ stage, index, isLast }) => {
  const getDomain = (url) => {
    if (!url) return 'Source';
    try {
      if (url.startsWith('http://') || url.startsWith('https://')) {
        return new URL(url).hostname.replace('www.', '');
      }
      return url.replace('www.', '').split('/')[0];
    } catch {
      return url.length > 22 ? url.substring(0, 22) + '…' : url;
    }
  };

  const getHref = (url) => {
    if (!url) return '#';
    if (url.startsWith('http://') || url.startsWith('https://')) return url;
    return `https://${url}`;
  };

  return (
    <div className="relative pl-8 pb-10 last:pb-0">
      {!isLast && <div className="absolute left-[11px] top-3 bottom-0 w-px bg-neutral-200/80"></div>}
      <div className="absolute left-0 top-1.5 w-[22px] h-[22px] bg-white border-2 border-neutral-300 rounded-full flex items-center justify-center z-10 shadow-sm">
        <div className="w-1.5 h-1.5 bg-neutral-950 rounded-full"></div>
      </div>
      <div className="bg-white border border-neutral-200/90 rounded-2xl p-6 shadow-sm hover:shadow-md transition-all duration-300 group">
        <div className="mb-3.5">
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-neutral-500 mb-1.5 flex items-center">
            Checkpoint {index + 1} <span className="mx-2 text-neutral-300">•</span> {formatDurationYears(stage.eta_months)}
          </span>
          <h4 className="text-lg sm:text-xl font-extrabold text-neutral-950 group-hover:text-black transition-colors tracking-tight">
            {stage.name}
          </h4>
        </div>
        <p className="text-sm sm:text-base text-neutral-800 leading-relaxed mb-5 whitespace-pre-line border-l-2 border-neutral-200 pl-3.5 font-normal">
          {stage.description}
        </p>
        {((stage.citations && stage.citations.length > 0) || (stage.top_opportunities && stage.top_opportunities.length > 0 && stage.top_opportunities[0].url)) && (
          <div className="bg-neutral-50/70 rounded-xl p-4 border border-neutral-200/70 space-y-3.5">
            {stage.citations?.length > 0 && (
              <div className="flex items-start gap-3">
                <div className="mt-0.5 min-w-max p-2 bg-purple-50 text-purple-700 rounded-lg border border-purple-200/60">
                  <BookOpen size={16} />
                </div>
                <div className="w-full">
                  <span className="text-xs uppercase font-bold text-neutral-600 tracking-wider block mb-2 font-mono">
                    Verified Trajectory Evidence
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {[...new Set(stage.citations.filter(Boolean))].map((url, i) => (
                      <a key={i} href={getHref(url)} target="_blank" rel="noreferrer"
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-neutral-300 rounded-md text-xs font-mono font-semibold text-neutral-800 hover:text-purple-700 hover:border-purple-300 transition-colors shadow-2xs">
                        <LinkIcon size={12} /> {getDomain(url)}
                      </a>
                    ))}
                  </div>
                </div>
              </div>
            )}
            {stage.top_opportunities?.length > 0 && stage.top_opportunities[0].url && (
              <div className="flex items-start gap-3 pt-3 border-t border-neutral-200/60">
                <div className="mt-0.5 min-w-max p-2 bg-blue-50 text-blue-700 rounded-lg border border-blue-200/60">
                  <Target size={16} />
                </div>
                <div>
                  <span className="text-xs uppercase font-bold text-neutral-600 tracking-wider block font-mono">Actionables</span>
                  <a href={getHref(stage.top_opportunities[0].url)} target="_blank" rel="noreferrer"
                    className="block text-sm sm:text-base font-bold text-neutral-950 leading-tight mt-1 hover:text-blue-600 hover:underline">
                    {stage.top_opportunities[0].title}
                  </a>
                  <p className="text-xs sm:text-sm text-neutral-700 mt-1 block line-clamp-2 leading-relaxed">
                    {stage.top_opportunities[0].snippet}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default function CareerTree() {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const [selectedPathIndex, setSelectedPathIndex] = useState(0);
  const [mobileExpandedPath, setMobileExpandedPath] = useState(0);
  const [isRecalibrating, setIsRecalibrating] = useState(false);

  const { data: tree, isLoading: loading, error, refetch } = useQuery({
    queryKey: ['careerTree'],
    queryFn: async () => {
      const res = await api.get('/career/tree');
      return res.data;
    },
    enabled: !!token
  });

  const handleRecalibrate = async () => {
    try {
      setIsRecalibrating(true);
      const res = await api.get('/career/tree?force=true');
      queryClient.setQueryData(['careerTree'], res.data);
      toast.success("Trajectories recalibrated with fresh market evidence!");
    } catch (err) {
      toast.error("The Trajectory Engine is recalibrating. Please try again.");
    } finally {
      setIsRecalibrating(false);
    }
  };

  if (error && !tree) {
    toast.error("The Trajectory Engine is recalibrating. Please try again.");
  }

  if (loading && !tree) return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-white">
      <Loader2 className="w-9 h-9 animate-spin text-neutral-950 mb-3.5" />
      <span className="text-sm sm:text-base font-mono font-bold text-neutral-800 tracking-tight">
        Researching Career Advisory Evidence...
      </span>
    </div>
  );

  // Compute live dynamic stats from the actual returned tree
  const uniqueCitations = new Set();
  tree?.paths?.forEach(p => {
    p.stages?.forEach(s => {
      s.citations?.forEach(c => { if (c) uniqueCitations.add(c); });
    });
  });
  const evidenceCount = uniqueCitations.size || tree?.graph_metrics?.evidence_sources_ingested || tree?.graph_metrics?.citations_resolved || 0;
  const totalMilestones = tree?.paths?.reduce((acc, p) => acc + (p.stages?.length || 0), 0) || 0;
  const pathCount = tree?.paths?.length;

  const activePath = tree?.paths?.[selectedPathIndex] || tree?.paths?.[0];

  return (
    <div className="min-h-screen bg-white pt-24 sm:pt-28 pb-20 px-4 sm:px-8 lg:px-12 xl:px-16 max-w-[1680px] w-full mx-auto">

      {/* Header */}
      <div className="max-w-3xl mx-auto text-center mb-10 sm:mb-12 animate-fade-in relative">
        <div className="inline-flex items-center justify-center px-4 py-1.5 bg-neutral-50 rounded-full shadow-2xs border border-neutral-200 mb-4 sm:mb-5">
          <BookOpen className="w-4 h-4 mr-2 text-indigo-600" />
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-neutral-700">Evidence-Based Roadmap</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-neutral-950 mb-3 sm:mb-4">The Serendipity Engine</h1>
        <p className="text-sm sm:text-base text-neutral-700 mb-6 leading-relaxed font-medium">
          Triangulated across multi-source market intelligence &amp; graph transitions.<br />
          Synthesized <span className="text-neutral-950 font-bold">{pathCount} Personalized Career Trajectories</span>.
        </p>

        <button
          onClick={handleRecalibrate}
          disabled={loading || isRecalibrating}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-white border border-neutral-300 rounded-full text-xs sm:text-sm font-bold text-neutral-900 hover:border-neutral-950 hover:bg-neutral-50 transition-all shadow-2xs active:scale-95 disabled:opacity-50 cursor-pointer"
        >
          <RefreshCw size={15} className={clsx((loading || isRecalibrating) && "animate-spin")} />
          {isRecalibrating ? "Triangulating Live Evidence..." : "Recalibrate Trajectories"}
        </button>
      </div>

      {error && !tree && (
        <div className="max-w-md mx-auto mb-10 bg-white p-6 rounded-2xl shadow-sm border border-rose-100 flex flex-col items-center text-center">
          <AlertCircle className="w-8 h-8 text-rose-500 mb-3" />
          <p className="text-neutral-700 text-sm mb-4 font-medium">The Trajectory Engine is recalibrating. Please try again.</p>
          <button onClick={handleRecalibrate} className="px-5 py-2 bg-neutral-950 text-white rounded-full text-xs font-bold">Retry</button>
        </div>
      )}

      {/* 1. LAPTOP DUAL-PANE VIEW (Visible on lg/xl screens) */}
      <div className="hidden lg:grid lg:grid-cols-12 gap-8 items-start">

        {/* Left Column: Trajectory Switcher Sidebar */}
        <div className="lg:col-span-4 space-y-4 sticky top-24">
          <div className="flex items-center justify-between pb-2 border-b border-neutral-200">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-neutral-700">Synthesized Trajectories</span>
            <span className="text-xs font-mono font-semibold text-neutral-500">{pathCount} Paths</span>
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
                      <h3 className={clsx("font-bold text-base leading-snug", isSelected ? "text-white" : "text-neutral-950")}>
                        {path.title}
                      </h3>
                    </div>
                  </div>

                  <p className={clsx("text-xs sm:text-sm line-clamp-2 mb-3 leading-relaxed", isSelected ? "text-neutral-300" : "text-neutral-700")}>
                    {path.summary}
                  </p>

                  <div className="flex items-center justify-between pt-2 border-t border-neutral-200/30 text-xs sm:text-sm font-mono">
                    <div className="flex items-center gap-3">
                      <span className={clsx("flex items-center font-bold", isSelected ? "text-emerald-400" : "text-emerald-700")}>
                        <Target size={13} className="mr-1" /> {(path.fit_score).toFixed(0)}% Match
                      </span>
                      <span className={clsx("flex items-center font-medium", isSelected ? "text-neutral-400" : "text-neutral-600")}>
                        <Clock size={13} className="mr-1" /> ~{formatDurationYears(path.stages?.reduce((a, c) => a + (c.eta_months || 0), 0), true)}
                      </span>
                    </div>
                    {isBestFit && (
                      <span className={clsx(
                        "px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider flex items-center shrink-0",
                        isSelected ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30" : "bg-emerald-50 text-emerald-800 border border-emerald-300"
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
          <div className="p-4 sm:p-5 rounded-2xl bg-neutral-50 border border-neutral-200/80 text-xs sm:text-sm font-mono text-neutral-800 space-y-2">
            <div className="flex justify-between items-center text-xs font-bold uppercase tracking-wider text-neutral-500">
              <span>Graph Intelligence</span>
              <span className="text-emerald-700 font-bold">Deterministic</span>
            </div>
            <div className="flex justify-between text-neutral-800">
              <span>Verified Evidence:</span>
              <span className="font-bold text-neutral-950">
                {evidenceCount > 0 ? `${evidenceCount} Ingested Sources` : 'Live Web Triangulation'}
              </span>
            </div>
            <div className="flex justify-between text-neutral-800">
              <span>Total Milestones:</span>
              <span className="font-bold text-neutral-950">{totalMilestones} Checkpoints</span>
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
                    <span className="px-3 py-1 rounded-lg bg-neutral-950 text-white font-mono text-xs sm:text-sm font-bold">
                      Path 0{selectedPathIndex + 1}
                    </span>
                    <h2 className="text-xl sm:text-2xl font-extrabold text-neutral-950 tracking-tight">
                      {activePath.title}
                    </h2>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs sm:text-sm font-mono font-bold px-3.5 py-1.5 bg-white border border-neutral-300 rounded-full text-neutral-900 shadow-2xs">
                      {(activePath.fit_score).toFixed(0)}% Profile Fit
                    </span>
                  </div>
                </div>

                <p className="text-sm sm:text-base text-neutral-800 leading-relaxed pt-2 border-t border-neutral-200/60 font-medium">
                  {activePath.summary}
                </p>
              </div>

              {/* Sequential Checkpoint Timeline */}
              <div className="bg-white p-6 sm:p-8 rounded-3xl border border-neutral-200/80 shadow-2xs">
                <div className="mb-6 pb-3 border-b border-neutral-100 flex items-center justify-between">
                  <span className="text-xs sm:text-sm font-mono font-bold uppercase tracking-wider text-neutral-800">
                    Sequential Execution Path ({activePath.stages?.length || 0} Checkpoints)
                  </span>
                  <span className="text-xs sm:text-sm font-mono text-neutral-600 font-medium">
                    Est. {formatDurationYears(activePath.stages?.reduce((a, c) => a + (c.eta_months || 0), 0))} Total
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
                        <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-800 uppercase border border-emerald-300 flex items-center shrink-0">
                          <Sparkles size={11} className="mr-1" /> Best Advice
                        </span>
                      )}
                    </div>
                    <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-xs sm:text-sm font-mono text-neutral-600">
                      <span className="flex items-center font-bold text-emerald-700"><Target size={13} className="mr-1 shrink-0" /> {(path.fit_score).toFixed(0)}% Match</span>
                      <span className="flex items-center font-medium"><Clock size={13} className="mr-1 shrink-0" /> ~{formatDurationYears(path.stages?.reduce((a, c) => a + (c.eta_months || 0), 0), true)}</span>
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