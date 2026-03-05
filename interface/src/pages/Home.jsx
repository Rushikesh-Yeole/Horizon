import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, Compass, GitBranch, Layers } from 'lucide-react';

const FadeIn = ({ children, delay = 0 }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
  >
    {children}
  </motion.div>
);

const FeatureCard = ({ icon: Icon, title, desc, delay, to }) => (
  <FadeIn delay={delay}>
    <Link to={to} className="group block h-full">
      <div className="h-full p-8 rounded-3xl bg-white border border-gray-100 shadow-sm hover:shadow-xl hover:scale-[1.02] transition-all duration-300 cursor-pointer relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-gray-50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
        <div className="relative z-10">
          <div className="w-12 h-12 rounded-2xl bg-gray-50 flex items-center justify-center mb-6 text-black group-hover:bg-black group-hover:text-white transition-colors">
            <Icon size={24} />
          </div>
          <h3 className="text-xl font-semibold mb-3">{title}</h3>
          <p className="text-gray-500 text-sm leading-relaxed">{desc}</p>
        </div>
      </div>
    </Link>
  </FadeIn>
);

export default function Home() {
  return (
    <div className="min-h-screen pt-32 pb-20 px-6 max-w-7xl mx-auto">
      {/* Hero Section */}
      <div className="max-w-3xl mx-auto text-center mb-24">
        {/* <FadeIn delay={0.1}>
          <span className="inline-block py-1 px-3 rounded-full bg-gray-100 text-gray-600 text-xs font-semibold tracking-wide uppercase mb-6">
            v1.0 Public Beta
          </span>
        </FadeIn> */}
        <FadeIn delay={0.2}>
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-gray-900 mb-8 leading-[1.1]">
            Your Career horizon <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-gray-400 to-gray-200">
              solved.
            </span>
          </h1>
        </FadeIn>
        <FadeIn delay={0.3}>
          <p className="text-xl text-gray-500 max-w-xl mx-auto leading-relaxed">
            Not a job board.
            <br/>
            A deterministic intelligence engine that calculates the semantic friction between you and your future.
            <br/><br/>
            <b>The Career Intelligence Platform</b>
          </p>
        </FadeIn>
      </div>

      {/* The Modules Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 px-4">
        <FeatureCard 
          to="/ingest"
          delay={0.4}
          icon={Layers}
          title="Profile Ingestion"
          desc="Feed the graph. We deconstruct your skills & experience into vector embeddings to understand your true velocity."
        />
        <FeatureCard 
          to="/discover"
          delay={0.5}
          icon={Compass}
          title="Discovery Engine"
          desc="Agentic swarms perform real-time, deep audits of global roles to quantify alignment and stress-test your profile against live market hiring bars."
        />
        <FeatureCard 
          to="/tree"
          delay={0.6}
          icon={GitBranch}
          title="Serendipitous Trajectory Tree"
          desc="Reverse-engineered career roadmaps that triangulate 42+ high-signal experiences to quantify and map your most ambitious professional outcomes."
        />
      </div>

      {/* Footer */}
      <FadeIn delay={0.8}>
        <div className="mt-32 text-center border-t border-gray-100 pt-10">
          <p className="text-gray-400 text-sm">
            <span className="font-mono text-xs opacity-50 mt-2 block">Rushikesh Yele | Shashwat Awate</span>
          </p>
        </div>
      </FadeIn>
    </div>
  );
}