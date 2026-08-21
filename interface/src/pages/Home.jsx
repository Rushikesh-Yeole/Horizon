import { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowRight, Compass, GitBranch, Layers, ShieldCheck,
  Cpu, Database, Network, CheckCircle2, XCircle,
  Terminal, Zap, Sparkles, Clock, Lock, FileText, Check, Activity
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/UI';

const FadeIn = ({ children, delay = 0 }) => (
  <motion.div
    initial={{ opacity: 0, y: 14 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.4, delay, ease: [0.16, 1, 0.3, 1] }}
  >
    {children}
  </motion.div>
);

// OpenAI-Style Abstract Chromatic Card Banner (Strictly Standardized Geometry & Sizes)
const PipelineBanner = ({ type }) => {
  if (type === 'ingest') {
    return (
      <div className="relative h-44 sm:h-48 w-full rounded-2xl overflow-hidden mb-6 bg-gradient-to-tr from-indigo-950 via-indigo-700 to-blue-400 p-4 sm:p-5 flex flex-col justify-between select-none border border-indigo-500/20 shadow-inner">
        {/* Abstract Mesh Glow */}
        <div className="absolute -top-12 -right-12 w-40 h-40 bg-blue-300/30 rounded-full blur-2xl pointer-events-none" />
        <div className="absolute -bottom-8 -left-8 w-32 h-32 bg-purple-500/30 rounded-full blur-xl pointer-events-none" />

        {/* Top Header Pills - Uniform Height & Alignment */}
        <div className="relative z-10 flex justify-between items-center gap-2">
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-white/20 text-white backdrop-blur-md border border-white/30 whitespace-nowrap shrink-0">
            Pipeline 01 • Ingest
          </span>
          <span className="text-[10px] font-mono text-indigo-200 bg-black/40 px-2 py-1 rounded-md backdrop-blur-sm whitespace-nowrap shrink-0">
            PyMuPDF + Pydantic
          </span>
        </div>

        {/* Bottom Info Capsule - Fixed Height & Standard Internal Grid */}
        <div className="relative z-10 bg-black/40 backdrop-blur-md rounded-xl p-3 border border-white/10 text-white h-[68px] flex flex-col justify-center">
          <div className="flex items-center justify-between text-xs font-mono font-bold mb-1 text-indigo-200">
            <span className="flex items-center gap-1.5 truncate">
              <FileText size={12} className="shrink-0" />
              <span>PDF → Schema Graph</span>
            </span>
            <span className="text-emerald-300 font-extrabold text-[11px] shrink-0 ml-2">Pydantic v2</span>
          </div>
          <div className="text-[11px] font-mono text-neutral-300 truncate">
            PyMuPDF • Skills &amp; Projects • Strict JSON
          </div>
        </div>
      </div>
    );
  }

  if (type === 'discover') {
    return (
      <div className="relative h-44 sm:h-48 w-full rounded-2xl overflow-hidden mb-6 bg-gradient-to-tr from-amber-900 via-amber-600 to-yellow-300 p-4 sm:p-5 flex flex-col justify-between select-none border border-amber-500/20 shadow-inner">
        {/* Abstract Mesh Glow */}
        <div className="absolute -top-10 -right-10 w-44 h-44 bg-yellow-200/40 rounded-full blur-2xl pointer-events-none" />
        <div className="absolute -bottom-8 -left-8 w-32 h-32 bg-orange-700/40 rounded-full blur-xl pointer-events-none" />

        {/* Top Header Pills - Uniform Height & Alignment */}
        <div className="relative z-10 flex justify-between items-center gap-2">
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-white/20 text-white backdrop-blur-md border border-white/30 whitespace-nowrap shrink-0">
            Pipeline 02 • Discover
          </span>
          <span className="text-[10px] font-mono text-amber-100 bg-black/40 px-2 py-1 rounded-md backdrop-blur-sm whitespace-nowrap shrink-0">
            Live JDs &amp; Interview Intel
          </span>
        </div>

        {/* Bottom Info Capsule - Fixed Height & Standard Internal Grid */}
        <div className="relative z-10 bg-black/40 backdrop-blur-md rounded-xl p-3 border border-white/10 text-white h-[68px] flex flex-col justify-center">
          <div className="flex items-center justify-between text-xs font-mono font-bold mb-1 text-amber-200">
            <span className="truncate">Agnostic Semantic Judge</span>
            <span className="text-emerald-300 font-extrabold text-[11px] shrink-0 ml-2">±1pt Deviation</span>
          </div>
          <div className="text-[11px] font-mono text-neutral-300 truncate">
            Greenhouse • Lever • Live Interview Signals
          </div>
        </div>
      </div>
    );
  }

  // Trajectory Tree
  return (
    <div className="relative h-44 sm:h-48 w-full rounded-2xl overflow-hidden mb-6 bg-gradient-to-tr from-emerald-950 via-teal-700 to-cyan-300 p-4 sm:p-5 flex flex-col justify-between select-none border border-teal-500/20 shadow-inner">
      {/* Abstract Mesh Glow */}
      <div className="absolute -top-12 -right-12 w-40 h-40 bg-cyan-200/30 rounded-full blur-2xl pointer-events-none" />
      <div className="absolute -bottom-8 -left-8 w-32 h-32 bg-emerald-600/30 rounded-full blur-xl pointer-events-none" />

      {/* Top Header Pills - Uniform Height & Alignment */}
      <div className="relative z-10 flex justify-between items-center gap-2">
        <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-white/20 text-white backdrop-blur-md border border-white/30 whitespace-nowrap shrink-0">
          Pipeline 03 • Trajectory
        </span>
        <span className="text-[10px] font-mono text-cyan-200 bg-black/40 px-2 py-1 rounded-md backdrop-blur-sm whitespace-nowrap shrink-0">
          Neo4j Traversal Priors
        </span>
      </div>

      {/* Bottom Info Capsule - Fixed Height & Standard Internal Grid */}
      <div className="relative z-10 bg-black/40 backdrop-blur-md rounded-xl p-3 border border-white/10 text-white h-[68px] flex flex-col justify-center">
        <div className="flex items-center justify-between text-xs font-mono font-bold mb-1 text-cyan-200">
          <span className="truncate">Parallel Web Evidence</span>
          <span className="text-emerald-300 font-extrabold text-[11px] shrink-0 ml-2">Up to 14 Sources</span>
        </div>
        <div className="text-[11px] font-mono text-neutral-300 truncate">
          Blind • HN • Reddit • FAANG Tech Blogs
        </div>
      </div>
    </div>
  );
};

const FeatureCard = ({ bannerType, title, desc, delay, to, disabled, tag, highlights }) => (
  <FadeIn delay={delay}>
    {disabled ? (
      <div className="h-full p-6 sm:p-7 rounded-3xl bg-neutral-50/70 border border-neutral-200/80 opacity-60 cursor-not-allowed relative flex flex-col justify-between">
        <div>
          <PipelineBanner type={bannerType} />
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono font-bold tracking-wider uppercase px-2.5 py-1 bg-neutral-200 text-neutral-700 rounded-md">
              {tag}
            </span>
            <span className="text-xs font-mono text-neutral-500">Locked in Demo</span>
          </div>
          <h3 className="text-xl font-extrabold text-neutral-950 mb-2.5 tracking-tight">{title}</h3>
          <p className="text-neutral-700 text-sm leading-relaxed">{desc}</p>
        </div>
      </div>
    ) : (
      <Link to={to} className="group block h-full">
        <div className="h-full p-6 sm:p-7 rounded-3xl bg-white border border-neutral-200/90 hover:border-neutral-950 hover:shadow-md transition-all duration-200 flex flex-col justify-between">
          <div>
            <PipelineBanner type={bannerType} />
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-mono font-bold tracking-wider uppercase px-2.5 py-1 bg-neutral-100 text-neutral-900 rounded-md">
                {tag}
              </span>
              <span className="text-xs font-mono text-neutral-500 font-semibold flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                Active Pipeline
              </span>
            </div>
            <h3 className="text-xl sm:text-2xl font-extrabold text-neutral-950 mb-2.5 tracking-tight group-hover:text-neutral-950 transition-colors">
              {title}
            </h3>
            <p className="text-neutral-800 text-sm sm:text-base leading-relaxed mb-6 font-normal">{desc}</p>

            {highlights && highlights.length > 0 && (
              <ul className="space-y-2 mb-6 border-t border-neutral-100 pt-4">
                {highlights.map((h, idx) => (
                  <li key={idx} className="flex items-center text-xs sm:text-sm text-neutral-800 font-medium">
                    <span className="w-1.5 h-1.5 rounded-full bg-neutral-950 mr-2.5 shrink-0" />
                    <span>{h}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div className="inline-flex items-center text-sm font-bold text-neutral-950 group-hover:translate-x-1.5 transition-transform pt-2 border-t border-neutral-100">
            <span>Explore Pipeline</span>
            <ArrowRight size={16} className="ml-2" />
          </div>
        </div>
      </Link>
    )}
  </FadeIn>
);

// Neo4j Knowledge Graph Visualizer Component (High-Legibility SVG + Plus Jakarta Sans / Geist)
const KnowledgeGraphVisualizer = () => {
  return (
    <div className="lg:col-span-7 bg-neutral-950 text-white rounded-3xl p-5 sm:p-7 border border-neutral-900 shadow-xl flex flex-col justify-between select-none">
      {/* Visualizer Header */}
      <div className="flex items-center justify-between pb-3.5 mb-3 border-b border-neutral-800/80">
        <div className="flex items-center gap-2.5">
          <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
          <span className="text-xs sm:text-sm text-neutral-200 font-bold tracking-tight">
            Role-to-Role Traversal &amp; Skill Priors
          </span>
        </div>
        <span className="text-[10px] sm:text-[11px] font-mono uppercase font-bold text-emerald-400 bg-emerald-950/80 px-2.5 py-0.5 rounded-md border border-emerald-800/60">
          Neo4j Knowledge Graph
        </span>
      </div>

      {/* SVG Knowledge Graph Diagram */}
      <div className="w-full overflow-x-auto py-1">
        <svg viewBox="0 0 800 350" className="w-full min-w-[640px] sm:min-w-full h-auto">
          <defs>
            {/* Arrowhead markers */}
            <marker id="arrow-cyan" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#38bdf8" />
            </marker>
            <marker id="arrow-emerald" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#34d399" />
            </marker>
            <linearGradient id="role-grad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#1e293b" />
              <stop offset="100%" stopColor="#0f172a" />
            </linearGradient>
            <linearGradient id="skill-grad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#142e2b" />
              <stop offset="100%" stopColor="#061a17" />
            </linearGradient>
          </defs>

          {/* Grid subtle background dots */}
          <pattern id="dot-grid" x="0" y="0" width="24" height="24" patternUnits="userSpaceOnUse">
            <circle cx="2" cy="2" r="1.2" fill="#2a2a2a" />
          </pattern>
          <rect width="800" height="350" fill="url(#dot-grid)" opacity="0.7" rx="16" />

          {/* Edges: TRANSITIONS_TO (Role -> Role) */}
          {/* Edge 1: AI Systems Eng -> Senior AI Infra */}
          <path d="M 205 155 L 305 155" stroke="#38bdf8" strokeWidth="2.5" strokeDasharray="4 4" markerEnd="url(#arrow-cyan)" />
          <rect x="215" y="142" width="90" height="19" rx="5" fill="#082f49" stroke="#0284c7" strokeWidth="1" />
          <text x="260" y="155" fill="#7dd3fc" fontSize="9" fontFamily="'JetBrains Mono', monospace" fontWeight="bold" textAnchor="middle">TRANSITIONS_TO</text>

          {/* Edge 2: Senior AI Infra -> Staff AI Architect */}
          <path d="M 485 155 L 585 155" stroke="#38bdf8" strokeWidth="2.5" strokeDasharray="4 4" markerEnd="url(#arrow-cyan)" />
          <rect x="495" y="142" width="90" height="19" rx="5" fill="#082f49" stroke="#0284c7" strokeWidth="1" />
          <text x="540" y="155" fill="#7dd3fc" fontSize="9" fontFamily="'JetBrains Mono', monospace" fontWeight="bold" textAnchor="middle">TRANSITIONS_TO</text>

          {/* Edges: REQUIRES (Role -> Skill) */}
          {/* AI Systems Eng -> vLLM & Triton Kernels */}
          <path d="M 120 125 L 180 72" stroke="#34d399" strokeWidth="2" markerEnd="url(#arrow-emerald)" />
          <rect x="110" y="85" width="82" height="18" rx="4" fill="#064e3b" stroke="#059669" strokeWidth="1" />
          <text x="151" y="97.5" fill="#6ee7b7" fontSize="9" fontFamily="'JetBrains Mono', monospace" fontWeight="bold" textAnchor="middle">REQUIRES (1.9)</text>

          {/* Senior AI Infra -> Distributed Training (FSDP) */}
          <path d="M 400 125 L 460 72" stroke="#34d399" strokeWidth="2" markerEnd="url(#arrow-emerald)" />
          <rect x="390" y="85" width="82" height="18" rx="4" fill="#064e3b" stroke="#059669" strokeWidth="1" />
          <text x="431" y="97.5" fill="#6ee7b7" fontSize="9" fontFamily="'JetBrains Mono', monospace" fontWeight="bold" textAnchor="middle">REQUIRES (2.8)</text>

          {/* AI Systems Eng -> Agentic Workflows (DSPy) */}
          <path d="M 120 185 L 155 273" stroke="#34d399" strokeWidth="2" markerEnd="url(#arrow-emerald)" />
          <rect x="95" y="222" width="82" height="18" rx="4" fill="#064e3b" stroke="#059669" strokeWidth="1" />
          <text x="136" y="234.5" fill="#6ee7b7" fontSize="9" fontFamily="'JetBrains Mono', monospace" fontWeight="bold" textAnchor="middle">REQUIRES (1.4)</text>

          {/* Staff AI Architect -> GPU Cluster Orchestration */}
          <path d="M 680 185 L 660 273" stroke="#34d399" strokeWidth="2" markerEnd="url(#arrow-emerald)" />
          <rect x="635" y="222" width="82" height="18" rx="4" fill="#064e3b" stroke="#059669" strokeWidth="1" />
          <text x="676" y="234.5" fill="#6ee7b7" fontSize="9" fontFamily="'JetBrains Mono', monospace" fontWeight="bold" textAnchor="middle">REQUIRES (3.4)</text>

          {/* Nodes: Roles (Central Horizontal Axis) */}
          {/* Node 1: AI Systems Engineer */}
          <g transform="translate(30, 125)">
            <rect width="175" height="60" rx="12" fill="url(#role-grad)" stroke="#38bdf8" strokeWidth="2" />
            <text x="87.5" y="24" fill="#94a3b8" fontSize="9.5" fontFamily="'JetBrains Mono', monospace" fontWeight="bold" textAnchor="middle" letterSpacing="0.05em">ROLE NODE</text>
            <text x="87.5" y="44" fill="#ffffff" fontSize="13.5" fontFamily="'Plus Jakarta Sans', 'Geist', sans-serif" fontWeight="800" textAnchor="middle">AI Systems Eng</text>
          </g>

          {/* Node 2: Senior AI Infra */}
          <g transform="translate(310, 125)">
            <rect width="175" height="60" rx="12" fill="url(#role-grad)" stroke="#38bdf8" strokeWidth="2" />
            <text x="87.5" y="24" fill="#94a3b8" fontSize="9.5" fontFamily="'JetBrains Mono', monospace" fontWeight="bold" textAnchor="middle" letterSpacing="0.05em">ROLE NODE</text>
            <text x="87.5" y="44" fill="#ffffff" fontSize="13.5" fontFamily="'Plus Jakarta Sans', 'Geist', sans-serif" fontWeight="800" textAnchor="middle">Senior AI Infra</text>
          </g>

          {/* Node 3: Staff AI Architect */}
          <g transform="translate(590, 125)">
            <rect width="180" height="60" rx="12" fill="url(#role-grad)" stroke="#38bdf8" strokeWidth="2" />
            <text x="90" y="24" fill="#38bdf8" fontSize="9.5" fontFamily="'JetBrains Mono', monospace" fontWeight="bold" textAnchor="middle" letterSpacing="0.05em">TERMINAL ROLE</text>
            <text x="90" y="44" fill="#ffffff" fontSize="13.5" fontFamily="'Plus Jakarta Sans', 'Geist', sans-serif" fontWeight="800" textAnchor="middle">Staff AI Architect</text>
          </g>

          {/* Nodes: Skills */}
          {/* Skill 1: vLLM & Triton Kernels */}
          <g transform="translate(100, 20)">
            <rect width="195" height="50" rx="10" fill="url(#skill-grad)" stroke="#34d399" strokeWidth="1.5" />
            <text x="97.5" y="20" fill="#6ee7b7" fontSize="9" fontFamily="'JetBrains Mono', monospace" fontWeight="bold" textAnchor="middle" letterSpacing="0.05em">FRONTIER SKILL</text>
            <text x="97.5" y="37" fill="#ffffff" fontSize="11.5" fontFamily="'Plus Jakarta Sans', 'Geist', sans-serif" fontWeight="700" textAnchor="middle">vLLM &amp; Triton Kernels</text>
          </g>

          {/* Skill 2: Distributed Training (FSDP) */}
          <g transform="translate(370, 20)">
            <rect width="215" height="50" rx="10" fill="url(#skill-grad)" stroke="#34d399" strokeWidth="1.5" />
            <text x="107.5" y="20" fill="#6ee7b7" fontSize="9" fontFamily="'JetBrains Mono', monospace" fontWeight="bold" textAnchor="middle" letterSpacing="0.05em">FRONTIER SKILL</text>
            <text x="107.5" y="37" fill="#ffffff" fontSize="11.5" fontFamily="'Plus Jakarta Sans', 'Geist', sans-serif" fontWeight="700" textAnchor="middle">Distributed FSDP / Megatron</text>
          </g>

          {/* Skill 3: Agentic Workflows (DSPy) */}
          <g transform="translate(60, 275)">
            <rect width="195" height="50" rx="10" fill="url(#skill-grad)" stroke="#34d399" strokeWidth="1.5" />
            <text x="97.5" y="20" fill="#6ee7b7" fontSize="9" fontFamily="'JetBrains Mono', monospace" fontWeight="bold" textAnchor="middle" letterSpacing="0.05em">FRONTIER SKILL</text>
            <text x="97.5" y="37" fill="#ffffff" fontSize="11.5" fontFamily="'Plus Jakarta Sans', 'Geist', sans-serif" fontWeight="700" textAnchor="middle">Agentic Tool-Use (DSPy)</text>
          </g>

          {/* Skill 4: GPU Cluster Orchestration */}
          <g transform="translate(535, 275)">
            <rect width="225" height="50" rx="10" fill="url(#skill-grad)" stroke="#34d399" strokeWidth="1.5" />
            <text x="112.5" y="20" fill="#6ee7b7" fontSize="9" fontFamily="'JetBrains Mono', monospace" fontWeight="bold" textAnchor="middle" letterSpacing="0.05em">FRONTIER SKILL</text>
            <text x="112.5" y="37" fill="#ffffff" fontSize="11.5" fontFamily="'Plus Jakarta Sans', 'Geist', sans-serif" fontWeight="700" textAnchor="middle">GPU Cluster Orchestration</text>
          </g>
        </svg>
      </div>

      {/* Visualizer Footer */}
      <div className="mt-3 pt-3 border-t border-neutral-800/80 flex flex-wrap items-center justify-between text-xs sm:text-sm text-neutral-400 gap-2 font-mono">
        <span>Trajectory Pathfinding: <strong className="text-cyan-400 font-semibold">Walks historical transitions up to 15 hops deep</strong></span>
        <span className="text-emerald-400 font-semibold">Self-improving edge weights on every run</span>
      </div>
    </div>
  );
};

export default function Home() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen pt-24 sm:pt-28 pb-16 px-4 sm:px-8 lg:px-12 xl:px-16 max-w-[1680px] w-full mx-auto">

      {/* 1. Hero Section */}
      <div className="max-w-4xl mx-auto text-center mb-16">
        <FadeIn delay={0.05}>
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full border border-neutral-300 bg-neutral-50 text-neutral-900 text-xs font-mono font-bold mb-6 shadow-2xs">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Horizon: The AI Career Intelligence Engine</span>
          </div>
        </FadeIn>

        <FadeIn delay={0.1}>
          <h1 className="text-4xl xs:text-5xl sm:text-6xl md:text-7xl font-extrabold text-neutral-950 mb-6 leading-[1.08] tracking-[-0.015em]">
            Career intelligence,<br />
            grounded in market reality.
          </h1>
        </FadeIn>

        <FadeIn delay={0.15}>
          <p className="text-base sm:text-2xl text-neutral-800 max-w-3xl mx-auto font-normal leading-relaxed mb-8 sm:mb-10">
            Horizon couples <strong className="font-semibold text-neutral-950">deep Neo4j trajectory traversal</strong> with <strong className="font-semibold text-neutral-950">multiple web sources</strong> to triangulate verified career trajectories, live hiring bars, and generate skill gap roadmaps.
          </p>
        </FadeIn>

        <FadeIn delay={0.2}>
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-center gap-3 sm:gap-4 max-w-md sm:max-w-none mx-auto">
            <Link to={isAuthenticated ? "/discover" : "/ingest"} className="w-full sm:w-auto">
              <Button variant="primary" className="w-full sm:w-auto px-7 py-3.5 text-sm sm:text-base shadow-sm font-bold">
                Get Started
                <ArrowRight size={18} className="ml-2" />
              </Button>
            </Link>
            <Link to="/tree" className="w-full sm:w-auto">
              <Button variant="outline" className="w-full sm:w-auto px-7 py-3.5 text-sm sm:text-base font-bold">
                View Career Tree
              </Button>
            </Link>
          </div>
        </FadeIn>
      </div>

      {/* 2. Live System Architecture Metric Strip */}
      <FadeIn delay={0.22}>
        <div className="bg-neutral-950 text-white rounded-3xl p-6 sm:p-8 mb-16 shadow-md grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-6 text-center border border-neutral-900">
          <div className="border-r border-neutral-800/80 pr-2 sm:pr-4">
            <div className="text-2xl sm:text-4xl font-extrabold text-white mb-1 font-mono tracking-tight">15 Hops</div>
            <div className="text-xs sm:text-sm text-neutral-400 font-mono font-medium">Max Traversal Depth</div>
          </div>
          <div className="md:border-r border-neutral-800/80 pr-2 sm:pr-4">
            <div className="text-2xl sm:text-4xl font-extrabold text-white mb-1 font-mono tracking-tight">14 Sources</div>
            <div className="text-xs sm:text-sm text-neutral-400 font-mono font-medium">Parallel Web Evidence</div>
          </div>
          <div className="border-r border-neutral-800/80 pr-2 sm:pr-4">
            <div className="text-2xl sm:text-4xl font-extrabold text-emerald-400 mb-1 font-mono tracking-tight">Grounded</div>
            <div className="text-xs sm:text-sm text-neutral-400 font-mono font-medium">Advisory Content</div>
          </div>
          <div>
            <div className="text-2xl sm:text-4xl font-extrabold text-white mb-1 font-mono tracking-tight">JD/Intel</div>
            <div className="text-xs sm:text-sm text-neutral-400 font-mono font-medium">Tiered Redis Caching</div>
          </div>
        </div>
      </FadeIn>

      {/* 3. OpenAI-Style Abstract Pipeline Modules Grid */}
      <div className="mb-20">
        <div className="flex items-center justify-between mb-8 pb-3 border-b border-neutral-200">
          <div>
            <span className="text-xs font-mono font-bold uppercase tracking-widest text-neutral-500">Core Subsystems</span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-neutral-950 tracking-tight">Engine Pipelines</h2>
          </div>
          <span className="text-xs font-mono text-neutral-500 hidden sm:block">Pydantic v2 • Strict JSON Validation</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 sm:gap-8">
          <FeatureCard
            bannerType="ingest"
            to={isAuthenticated ? "/profile" : "/ingest"}
            delay={0.25}
            title="Profile Ingestion"
            desc="PyMuPDF converts resume bytes into Markdown, then Gemini 2.5 Flash extracts canonical skills, education, and projects into structured Pydantic schemas."
            tag="Pipeline 01"
            highlights={[
              "PDF to Markdown extraction via PyMuPDF",
              "Synonym skill canonicalizer",
              "Motor async MongoDB document storage"
            ]}
          />
          <FeatureCard
            bannerType="discover"
            to="/discover"
            delay={0.3}
            title="Discovery Engine"
            desc="Scrapes active Greenhouse & Lever JDs in parallel, triangulating genuine interview bars & hiring expectations with strict deterministic rubrics."
            tag="Pipeline 02"
            highlights={[
              "Live Greenhouse/Lever JDs + web search",
              "Agnostic Semantic Judge (A/B/C/D rubric)",
              "Empirical interview bar & actionable gap roadmap"
            ]}
          />
          <FeatureCard
            bannerType="tree"
            to="/tree"
            delay={0.35}
            title="Trajectory Tree"
            desc="Graph-first trajectory discovery synthesizing real Reddit, Blind, and Tech Blog career stories into a 5-path evidence-cited roadmap."
            tag="Pipeline 03"
            highlights={[
              "Neo4j trajectory priors (up to 15 hops)",
              "100% direct URL source citations",
              "Self-improving graph writeback on every run"
            ]}
          />
        </div>
      </div>

      {/* 4. First-Principles Thesis Section (Chatbots vs Horizon) */}
      <FadeIn delay={0.38}>
        <div className="mb-20 rounded-3xl bg-neutral-50/80 border border-neutral-200/90 p-6 sm:p-10 shadow-2xs">
          <div className="max-w-3xl mb-8">
            <span className="text-xs font-mono font-bold uppercase tracking-widest text-neutral-500">First-Principles Architecture</span>
            <h2 className="text-2xl sm:text-4xl font-extrabold text-neutral-950 mt-1.5 mb-3 leading-snug">
              Why Unconstrained LLM Chatbots Fail at Career Advice
            </h2>
            <p className="text-neutral-800 text-sm sm:text-base leading-relaxed font-normal">
              Most AI career products are simple chatbot wrappers: they hallucinate generic advice, cite zero real evidence, and forget everything after the conversation. Horizon is engineered with graph-first constraints and self-improving memory.
            </p>
          </div>

          {/* Comparison Matrix Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs sm:text-sm border-collapse">
              <thead>
                <tr className="border-b border-neutral-300/80 text-neutral-500 font-mono text-[11px] uppercase tracking-wider">
                  <th className="py-3 px-4 font-bold">System Dimension</th>
                  <th className="py-3 px-4 font-bold text-neutral-500">Standard GenAI Chatbots</th>
                  <th className="py-3 px-4 font-bold text-neutral-950 bg-neutral-100/80 rounded-t-xl">Horizon Career Intelligence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-200 font-mono">
                <tr className="hover:bg-white/60 transition-colors">
                  <td className="py-3.5 px-4 font-bold text-neutral-950 font-sans">Grounding Mechanism</td>
                  <td className="py-3.5 px-4 text-neutral-600">Unconstrained next-token sampling</td>
                  <td className="py-3.5 px-4 text-neutral-950 font-semibold bg-neutral-100/40">
                    <strong className="text-emerald-700">Neo4j Trajectory Priors (up to 15 transitions) + Parallel Web Evidence (up to 14 sources)</strong>
                  </td>
                </tr>
                <tr className="hover:bg-white/60 transition-colors">
                  <td className="py-3.5 px-4 font-bold text-neutral-950 font-sans">Evidence & Citations</td>
                  <td className="py-3.5 px-4 text-neutral-600">Vague generalities, 0 sources cited</td>
                  <td className="py-3.5 px-4 text-neutral-950 font-semibold bg-neutral-100/40">
                    <strong className="text-indigo-700">100% Direct URL Attribution</strong> (Blind, HN, Reddit, Blogs)
                  </td>
                </tr>
                <tr className="hover:bg-white/60 transition-colors">
                  <td className="py-3.5 px-4 font-bold text-neutral-950 font-sans">Hiring Bar Evaluation</td>
                  <td className="py-3.5 px-4 text-neutral-600">Flattering, subjective encouragement</td>
                  <td className="py-3.5 px-4 text-neutral-950 font-semibold bg-neutral-100/40">
                    <strong className="text-amber-800">Deterministic A/B/C/D Rubric</strong> with level/ecosystem caps
                  </td>
                </tr>
                <tr className="hover:bg-white/60 transition-colors">
                  <td className="py-3.5 px-4 font-bold text-neutral-950 font-sans">System Memory & Evolution</td>
                  <td className="py-3.5 px-4 text-neutral-600">Ephemeral context, forgotten instantly</td>
                  <td className="py-3.5 px-4 text-neutral-950 font-semibold bg-neutral-100/40">
                    <strong className="text-neutral-950">Self-Improving Neo4j Graph Writeback</strong> (<code className="code-pill">TRANSITIONS_TO</code>)
                  </td>
                </tr>
                <tr className="hover:bg-white/60 transition-colors">
                  <td className="py-3.5 px-4 font-bold text-neutral-950 font-sans">Schema Integrity</td>
                  <td className="py-3.5 px-4 text-neutral-600">Markdown text with regex fallbacks</td>
                  <td className="py-3.5 px-4 text-neutral-950 font-semibold bg-neutral-100/40">
                    <strong className="text-neutral-950">100% Pydantic v2 Strict JSON Validation</strong>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </FadeIn>

      {/* 5. Neo4j Knowledge Graph & Agnostic Semantic Judge Rubric Display */}
      <FadeIn delay={0.42}>
        <div className="mb-20 grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">

          {/* Left: SVG Knowledge Graph Visualizer */}
          <KnowledgeGraphVisualizer />

          {/* Right: The Deterministic Scoring Rubric */}
          <div className="lg:col-span-5 bg-neutral-50/90 rounded-3xl p-6 sm:p-8 border border-neutral-200 shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 mb-4 pb-3 border-b border-neutral-200">
                <Zap size={18} className="text-amber-600 shrink-0" />
                <h3 className="text-sm sm:text-base font-extrabold text-neutral-950 uppercase tracking-wider font-mono">
                  Agnostic Semantic Judge Rubric
                </h3>
              </div>

              {/* Rubric Grades */}
              <div className="space-y-3">
                <div className="p-3.5 sm:p-4 bg-white rounded-2xl border border-neutral-200 flex items-center justify-between gap-3 shadow-2xs">
                  <span className="font-bold text-emerald-800 bg-emerald-100/80 px-3 py-1 rounded-lg border border-emerald-300 text-xs sm:text-sm font-mono shrink-0">
                    Grade A (90–100)
                  </span>
                  <span className="text-neutral-900 font-semibold text-xs sm:text-sm text-right font-sans">
                    &gt;80% match + prod proof
                  </span>
                </div>

                <div className="p-3.5 sm:p-4 bg-white rounded-2xl border border-neutral-200 flex items-center justify-between gap-3 shadow-2xs">
                  <span className="font-bold text-blue-800 bg-blue-100/80 px-3 py-1 rounded-lg border border-blue-300 text-xs sm:text-sm font-mono shrink-0">
                    Grade B (75–89)
                  </span>
                  <span className="text-neutral-900 font-semibold text-xs sm:text-sm text-right font-sans">
                    &gt;50% match (sibling tech)
                  </span>
                </div>

                <div className="p-3.5 sm:p-4 bg-white rounded-2xl border border-neutral-200 flex items-center justify-between gap-3 shadow-2xs">
                  <span className="font-bold text-amber-900 bg-amber-100/80 px-3 py-1 rounded-lg border border-amber-300 text-xs sm:text-sm font-mono shrink-0">
                    Grade C (60–74)
                  </span>
                  <span className="text-neutral-900 font-semibold text-xs sm:text-sm text-right font-sans">
                    &lt;50% match (3+ mo ramp)
                  </span>
                </div>

                <div className="p-3.5 sm:p-4 bg-white rounded-2xl border border-neutral-200 flex items-center justify-between gap-3 shadow-2xs">
                  <span className="font-bold text-rose-900 bg-rose-100/80 px-3 py-1 rounded-lg border border-rose-300 text-xs sm:text-sm font-mono shrink-0">
                    Grade D (&lt;60)
                  </span>
                  <span className="text-neutral-900 font-semibold text-xs sm:text-sm text-right font-sans">
                    Core pillars missing
                  </span>
                </div>
              </div>
            </div>

            {/* Hard Modifiers */}
            <div className="mt-5 pt-4 border-t border-neutral-200 text-xs sm:text-sm text-neutral-800 space-y-2 font-medium">
              <div className="text-neutral-950 font-bold uppercase tracking-wider font-mono text-xs">Hard Modifiers</div>
              <div className="flex items-center justify-between py-0.5 font-sans text-xs sm:text-sm text-neutral-800">
                <span>• FAANG / Unicorn Experience</span>
                <span className="font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 font-mono text-xs">+5 pts</span>
              </div>
              <div className="flex items-center justify-between py-0.5 font-sans text-xs sm:text-sm text-neutral-800">
                <span>• Seniority Level Mismatch</span>
                <span className="font-bold text-rose-800 bg-rose-50 px-2 py-0.5 rounded border border-rose-200 font-mono text-xs">Capped at 20 pts</span>
              </div>
              <div className="flex items-center justify-between py-0.5 font-sans text-xs sm:text-sm text-neutral-800">
                <span>• Ecosystem Lock-in</span>
                <span className="font-bold text-amber-900 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 font-mono text-xs">Capped at 30 pts</span>
              </div>
            </div>
          </div>

        </div>
      </FadeIn>

      {/* 6. Production Economics & Cache Volatility Strip */}
      <FadeIn delay={0.44}>
        <div className="border-t border-neutral-200/90 pt-12 grid grid-cols-1 md:grid-cols-3 gap-6 sm:gap-8 text-left mb-16">
          <div className="p-6 rounded-2xl bg-neutral-50/70 border border-neutral-200/80">
            <div className="flex items-center gap-2 mb-3 text-neutral-950 font-bold text-base">
              <Database size={18} />
              <span>01 / Graph Before LLM</span>
            </div>
            <p className="text-sm text-neutral-800 leading-relaxed font-normal">
              Neo4j queries find weighted skill overlaps (<code className="code-pill">REQUIRES</code> edges) and walk historical transitions (<code className="code-pill">TRANSITIONS_TO</code>) up to 15 hops before falling back to Gemini synthesis.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-neutral-50/70 border border-neutral-200/80">
            <div className="flex items-center gap-2 mb-3 text-neutral-950 font-bold text-base">
              <ShieldCheck size={18} />
              <span>02 / Evidence Over Inference</span>
            </div>
            <p className="text-sm text-neutral-800 leading-relaxed font-normal">
              Tavily pulls up to 14 high-signal results per archetype from Blind, HackerNews, and Engineering Blogs. Every generated stage cites exact source URLs.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-neutral-50/70 border border-neutral-200/80">
            <div className="flex items-center gap-2 mb-3 text-neutral-950 font-bold text-base">
              <Network size={18} />
              <span>03 / Tiered Redis Caching</span>
            </div>
            <p className="text-sm text-neutral-800 leading-relaxed font-normal">
              Invalidation tiered by volatility: <code className="code-pill">24h</code> for Trajectory Trees, <code className="code-pill">30m</code> for Live Greenhouse/Lever JDs, and <code className="code-pill">7m</code> for interview signals.
            </p>
          </div>
        </div>
      </FadeIn>

      {/* 7. Footer */}
      <FadeIn delay={0.46}>
        <div className="mt-14 flex flex-col items-center justify-center border-t border-neutral-200/90 pt-8 gap-3">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-neutral-950 flex items-center justify-center p-0.5 shadow-2xs border border-neutral-800">
              <img src="/horizon-logo.png" alt="Horizon Logo" className="w-full h-full object-contain" />
            </div>
            <span className="font-extrabold text-neutral-950 tracking-tight text-sm">Horizon</span>
          </div>
          <p className="text-neutral-600 text-sm font-medium tracking-wide text-center">
            Career Intelligence • Built by{' '}
            <a
              href="https://www.linkedin.com/in/rushikesh-yeole-9115702aa"
              target="_blank"
              rel="noreferrer"
              className="text-neutral-950 font-bold hover:underline decoration-neutral-400 underline-offset-2 transition-all underline"
            >
              Rushikesh Yeole
            </a>
            {' & '}
            <a
              href="https://www.linkedin.com/in/shashwat-awate-23127a29b/"
              target="_blank"
              rel="noreferrer"
              className="text-neutral-950 font-bold hover:underline decoration-neutral-400 underline-offset-2 transition-all underline"
            >
              Shashwat Awate
            </a>
          </p>
        </div>
      </FadeIn>

    </div>
  );
}