import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, Compass, GitBranch, Layers, ShieldCheck, Cpu, Database, Network } from 'lucide-react';
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

const FeatureCard = ({ icon: Icon, title, desc, delay, to, disabled, tag, highlights }) => (
  <FadeIn delay={delay}>
    {disabled ? (
      <div className="h-full p-7 sm:p-8 rounded-2xl bg-neutral-50/60 border border-neutral-200/80 opacity-60 cursor-not-allowed relative">
        <div className="flex items-center justify-between mb-6">
          <div className="w-12 h-12 rounded-xl bg-neutral-200/60 flex items-center justify-center text-neutral-700">
            <Icon size={24} />
          </div>
          <span className="text-xs font-semibold tracking-wider uppercase px-3 py-1 bg-neutral-200/70 text-neutral-700 rounded-md">
            Demo Mode Locked
          </span>
        </div>
        <h3 className="text-xl font-bold text-neutral-950 mb-3">{title}</h3>
        <p className="text-neutral-600 text-base leading-relaxed">{desc}</p>
      </div>
    ) : (
      <Link to={to} className="group block h-full">
        <div className="h-full p-7 sm:p-8 rounded-2xl bg-white border border-neutral-200/90 hover:border-neutral-950 hover:shadow-sm transition-all duration-200 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-6">
              <div className="w-12 h-12 rounded-xl bg-neutral-100 flex items-center justify-center text-neutral-950 group-hover:bg-neutral-950 group-hover:text-white transition-colors">
                <Icon size={24} />
              </div>
              {tag && (
                <span className="text-xs font-bold tracking-wider uppercase px-3 py-1 bg-neutral-100 text-neutral-800 rounded-md">
                  {tag}
                </span>
              )}
            </div>
            <h3 className="text-xl sm:text-2xl font-bold text-neutral-950 mb-3 group-hover:text-neutral-950 transition-colors">
              {title}
            </h3>
            <p className="text-neutral-700 text-base leading-relaxed mb-6">{desc}</p>

            {highlights && highlights.length > 0 && (
              <ul className="space-y-2 mb-6 border-t border-neutral-100 pt-4">
                {highlights.map((h, idx) => (
                  <li key={idx} className="flex items-center text-xs sm:text-sm text-neutral-600 font-medium">
                    <span className="w-1.5 h-1.5 rounded-full bg-neutral-900 mr-2.5" />
                    {h}
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div className="inline-flex items-center text-sm font-bold text-neutral-950 group-hover:translate-x-1 transition-transform pt-2">
            <span>Explore pipeline</span>
            <ArrowRight size={16} className="ml-2" />
          </div>
        </div>
      </Link>
    )}
  </FadeIn>
);

export default function Home() {
  const { email, isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen pt-24 sm:pt-28 pb-16 px-4 sm:px-8 lg:px-12 xl:px-16 max-w-[1680px] w-full mx-auto">
      {/* Hero Section */}
      <div className="max-w-4xl mx-auto text-center mb-16">
        <FadeIn delay={0.05}>
          <h1 className="text-3xl xs:text-4xl sm:text-6xl md:text-7xl font-extrabold tracking-tight text-neutral-950 mb-6 leading-[1.08]">
            Career intelligence,<br />
            grounded in market reality.
          </h1>
        </FadeIn>

        <FadeIn delay={0.15}>
          <p className="text-base sm:text-2xl text-neutral-700 max-w-3xl mx-auto font-normal leading-relaxed mb-8 sm:mb-10">
            Horizon couples a living Neo4j graph with 14x parallel web scrapers to triangulate verified career trajectories, live hiring bars, and skill gap roadmaps.
          </p>
        </FadeIn>

        <FadeIn delay={0.2}>
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-center gap-3 sm:gap-4 max-w-md sm:max-w-none mx-auto">
            <Link to={isAuthenticated ? "/discover" : "/ingest"} className="w-full sm:w-auto">
              <Button variant="primary" className="w-full sm:w-auto px-7 py-3.5 text-sm sm:text-base shadow-sm">
                Get Started
                <ArrowRight size={18} className="ml-2" />
              </Button>
            </Link>
            <Link to="/tree" className="w-full sm:w-auto">
              <Button variant="outline" className="w-full sm:w-auto px-7 py-3.5 text-sm sm:text-base">
                View Career Tree
              </Button>
            </Link>
          </div>
        </FadeIn>
      </div>

      {/* Live System Architecture Metric Strip */}
      <FadeIn delay={0.22}>
        <div className="bg-neutral-950 text-white rounded-2xl p-5 sm:p-8 mb-16 shadow-md grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-6 text-center border border-neutral-900">
          <div className="border-r border-neutral-800/80 pr-2 sm:pr-4">
            <div className="text-xl sm:text-4xl font-extrabold text-white mb-1">15-Hop</div>
            <div className="text-[11px] sm:text-sm text-neutral-400 font-medium">Neo4j Traversal</div>
          </div>
          <div className="md:border-r border-neutral-800/80 pr-2 sm:pr-4">
            <div className="text-xl sm:text-4xl font-extrabold text-white mb-1">14x</div>
            <div className="text-[11px] sm:text-sm text-neutral-400 font-medium">Parallel Streams</div>
          </div>
          <div className="border-r border-neutral-800/80 pr-2 sm:pr-4">
            <div className="text-xl sm:text-4xl font-extrabold text-white mb-1">0%</div>
            <div className="text-[11px] sm:text-sm text-neutral-400 font-medium">Hallucination</div>
          </div>
          <div>
            <div className="text-xl sm:text-4xl font-extrabold text-white mb-1">24h</div>
            <div className="text-[11px] sm:text-sm text-neutral-400 font-medium">Redis Caching</div>
          </div>
        </div>
      </FadeIn>

      {/* Modules Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
        <FeatureCard
          to={isAuthenticated ? "/profile" : "/ingest"}
          delay={0.25}
          icon={Layers}
          title="Profile Ingestion"
          desc="PyMuPDF ingests your resume into Markdown, then Gemini 2.5 Flash extracts canonical skills, education, and projects into structured Pydantic schemas."
          tag="Pipeline 01"
          highlights={[
            "PDF to Markdown extraction",
            "Synonym skill normalizer",
            "Motor async MongoDB storage"
          ]}
        />
        <FeatureCard
          to="/discover"
          delay={0.3}
          icon={Compass}
          title="Discovery Engine"
          desc="Scrapes active Greenhouse & Lever JDs in parallel, scoring your profile against target company bars using strict algorithmic rubrics."
          tag="Pipeline 02"
          highlights={[
            "Live Greenhouse/Lever JDs",
            "A/B/C/D scoring rubric",
            "Top 10 absent skill gaps"
          ]}
        />
        <FeatureCard
          to="/tree"
          delay={0.35}
          icon={GitBranch}
          title="Trajectory Tree"
          desc="Graph-first trajectory discovery synthesizing real Reddit, Blind, and Tech Blog career stories into a 5-path evidence-cited roadmap."
          tag="Pipeline 03"
          highlights={[
            "Neo4j trajectory priors",
            "Real URL source citations",
            "Self-improving graph writeback"
          ]}
        />
      </div>

      {/* Grounded System Engineering Statement */}
      <FadeIn delay={0.4}>
        <div className="border-t border-neutral-200/90 pt-12 grid grid-cols-1 md:grid-cols-3 gap-8 text-left">
          <div className="p-6 rounded-xl bg-neutral-50/70 border border-neutral-200/80">
            <div className="flex items-center gap-2 mb-3 text-neutral-950 font-bold text-base">
              <Database size={18} />
              <span>01 / Graph Before LLM</span>
            </div>
            <p className="text-sm text-neutral-700 leading-relaxed">
              Neo4j queries find weighted skill overlaps (`REQUIRES` edges) and walk historical transitions (`TRANSITIONS_TO`) up to 15 hops before falling back to Gemini synthesis.
            </p>
          </div>

          <div className="p-6 rounded-xl bg-neutral-50/70 border border-neutral-200/80">
            <div className="flex items-center gap-2 mb-3 text-neutral-950 font-bold text-base">
              <ShieldCheck size={18} />
              <span>02 / Evidence Over Inference</span>
            </div>
            <p className="text-sm text-neutral-700 leading-relaxed">
              Tavily pulls up to 14 high-signal results per archetype from Blind, HackerNews, and Engineering Blogs. Every generated stage cites exact source URLs.
            </p>
          </div>

          <div className="p-6 rounded-xl bg-neutral-50/70 border border-neutral-200/80">
            <div className="flex items-center gap-2 mb-3 text-neutral-950 font-bold text-base">
              <Network size={18} />
              <span>03 / Self-Improving Flywheel</span>
            </div>
            <p className="text-sm text-neutral-700 leading-relaxed">
              Extracted career paths (`observed_paths`) write back to Neo4j on every synthesis run. More users → denser graph → sharper career trajectories.
            </p>
          </div>
        </div>
      </FadeIn>

      {/* Footer */}
      <FadeIn delay={0.45}>
        <div className="mt-14 text-center border-t border-neutral-200/90 pt-6">
          <p className="text-neutral-500 text-md font-medium tracking-wide">
            Horizon Infrastructure for Career Intelligence <br></br> Built by{' '}
            <a
              href="https://www.linkedin.com/in/rushikesh-yeole-9115702aa"
              target="_blank"
              rel="noreferrer"
              className="text-neutral-900 font-semibold hover:underline decoration-neutral-400 underline-offset-2 transition-all"
            >
              Rushikesh Yeole
            </a>
            {' & '}
            <a
              href="https://www.linkedin.com/in/shashwat-awate-23127a29b/"
              target="_blank"
              rel="noreferrer"
              className="text-neutral-900 font-semibold hover:underline decoration-neutral-400 underline-offset-2 transition-all"
            >
              Shashwat Awate
            </a>
          </p>
        </div>
      </FadeIn>
    </div>
  );
}