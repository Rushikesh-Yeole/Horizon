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
  const [expandedPath, setExpandedPath] = useState(null);

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

  return (
    <div className="min-h-screen bg-white pt-24 sm:pt-28 pb-20 px-4 sm:px-6 md:px-8">
      
      {/* Header */}
      <div className="max-w-2xl mx-auto text-center mb-10 sm:mb-12 animate-fade-in relative">
        <div className="inline-flex items-center justify-center px-4 py-1.5 bg-neutral-50 rounded-full shadow-2xs border border-neutral-200 mb-4 sm:mb-5">
          <BookOpen className="w-3.5 h-3.5 mr-2 text-indigo-600" />
          <span className="text-[10px] font-mono font-bold uppercase tracking-widest text-neutral-600">Evidence-Based Roadmap</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-neutral-950 mb-3 sm:mb-4">The Serendipity Engine</h1>
        <p className="text-sm sm:text-base text-neutral-600 mb-6 leading-relaxed">
          Analyzed 42+ real-world trajectories & web evidence.<br />
          Synthesized <span className="text-neutral-950 font-semibold">3 Personalized Paths</span>.
        </p>
        
        <button 
          onClick={() => refetch()}
          disabled={loading}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-white border border-neutral-200 rounded-full text-xs font-bold text-neutral-800 hover:border-neutral-950 hover:bg-neutral-50 transition-all shadow-2xs active:scale-95 disabled:opacity-50"
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

      {/* Stacked Accordion */}
      <div className="max-w-3xl mx-auto space-y-4 sm:space-y-5">
        {tree?.paths?.map((path, idx) => {
          const isExpanded = expandedPath === idx;
          const isBestFit = idx === 0;

          return (
            <motion.div 
              key={path.id || idx}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              className={clsx(
                "bg-white rounded-2xl sm:rounded-3xl overflow-hidden border transition-all duration-300",
                isExpanded ? "shadow-xl shadow-black/5 border-neutral-300 ring-1 ring-neutral-950/5" : "shadow-2xs border-neutral-200/80 hover:border-neutral-400 cursor-pointer"
              )}
            >
              <div onClick={() => setExpandedPath(isExpanded ? null : idx)} className="p-4 sm:p-6 flex items-center justify-between gap-3">
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
                    <div className="px-4 sm:px-6 md:px-8 pb-6 sm:pb-8 pt-2 border-t border-neutral-100 bg-neutral-50/40">
                      <div className="mb-6 sm:mb-8 bg-white p-4 rounded-xl border border-neutral-200/80 shadow-2xs">
                        <span className="font-mono font-bold text-neutral-950 block mb-1 uppercase tracking-wider text-[10px]">Strategic Intent</span>
                        <p className="text-xs sm:text-sm text-neutral-700 leading-relaxed">{path.summary}</p>
                      </div>
                      <div className="pl-1 sm:pl-2">
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