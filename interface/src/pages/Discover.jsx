import { useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Card, Button, Input } from '../components/UI';
import { Search, Zap, AlertTriangle, CheckCircle, Loader2 } from 'lucide-react';

export default function Discover() {
  const { token } = useAuth();
  const [criteria, setCriteria] = useState({ 
    role: "Frontend Engineer", 
    location: "Bangalore", 
    companies: "Google" 
  });
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const runPhysicsEngine = async () => {
    // DEV BYPASS: Commented out token check
    // if (!token) {
    //     alert("Session expired. Please re-initialize.");
    //     return;
    // }

    setLoading(true);
    try {
      const res = await axios.post(
            "http://localhost:8000/discover/search",
            {
              search_criteria: {
                role: criteria.role,
                location: criteria.location,
                target_companies: criteria.companies
                  .split(",")
                  .map((c) => c.trim()),
              },
              // DEV BYPASS: Hardcoded user profile for quick iteration
  "user_profile": {
    "profile": {
      "skills": ["HTML", "CSS", "Next.js", "Tailwind", "Algorithms", "Data structures", "Java", "SQL", "Spring Boot", "Python", "C++", "React.js", "Node.js", "Express", "MongoDB", "Tailwind CSS", "Redux"],
      "projects": [
        {"title": "E-commerce Storefront", "desc": "Built fully responsive frontend with React and Redux state management"},
        {"title": "FMCG retail Management System", "desc": "Developed Node/Express backend with MongoDB aggregation pipelines"}
      ],
      "preferences": {"role": "Backend Engineer"},
      "experience": ["SDE Intern at Amazon India - 6 months"]
    }
  }
            }
      );
      setResults(res.data.guidance_cards);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || "Physics Engine Stalled. Backend unreachable.";
      console.error("Audit Error:", err);
      alert(`System Failure: ${errorMsg}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto pt-28 pb-20 px-4 animate-fade-in">
      {/* Header Section */}
      <div className="flex justify-between items-end mb-10">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Discovery Search</h1>
          <p className="text-secondary">Multi-Layer deterministic search for candidate-role fit.</p>
        </div>
      </div>

      {/* Input Control Panel */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-12">
        <div className="md:col-span-1">
          <Input label="Target Role" value={criteria.role} onChange={e => setCriteria({...criteria, role: e.target.value})} />
        </div>
        <div className="md:col-span-1">
          <Input label="Geography" value={criteria.location} onChange={e => setCriteria({...criteria, location: e.target.value})} />
        </div>
        <div className="md:col-span-1">
          <Input label="Target Firms (multiple)" placeholder="Comma separated" value={criteria.companies} onChange={e => setCriteria({...criteria, companies: e.target.value})} />
        </div>
        <div className="md:col-span-1 flex items-center pt-2">
          <Button onClick={runPhysicsEngine} isLoading={loading} className="w-full h-12">
            {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2 inline" /> : <Search className="w-4 h-4 mr-2 inline" />} 
            Search
          </Button>
        </div>
      </div>

      {/* Results Mapping */}
      <div className="space-y-6">
        {results?.map((card, i) => (
          <Card key={i} className="border-l-4 border-l-black group">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-2xl font-semibold capitalize tracking-tight">{card.company_name}</h2>
                <div className="flex gap-2 items-center mt-1">
                   <span className="text-[10px] uppercase tracking-widest bg-gray-100 px-2 py-0.5 rounded font-bold text-gray-600">
                    {card.hiring_bar_difficulty} Bar
                  </span>
                   <span className="text-[10px] uppercase tracking-widest text-secondary font-bold">
                    {card.feasibility_timeline_weeks} Weeks to bridge
                  </span>
                </div>
              </div>
              <div className="text-right">
                <div className="text-4xl font-bold tracking-tighter tabular-nums">{card.fit_score}%</div>
                <div className="text-[10px] font-bold text-secondary uppercase tracking-widest">Fit Score</div>
              </div>
            </div>
            
            <p className="text-lg font-medium mb-6 text-gray-800 leading-snug">"{card.verdict_headline}"</p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* Reasoning Trace */}
              <div className="bg-gray-50 p-5 rounded-2xl border border-gray-100">
                <h3 className="text-[12px] font-bold uppercase text-secondary mb-3 flex items-center tracking-widest">
                  <Zap className="w-3 h-3 mr-1.5 fill-black"/> Reasoning Trace
                </h3>
                <p className="text-sm font-mono text-gray-600 leading-relaxed italic">{card.reasoning_trace}</p>
                {/* main_advisory_text */}
                <h3 className="text-[12px] font-bold uppercase text-secondary mb-3 mt-5 flex items-center tracking-widest">
                  <Zap className="w-3 h-3 mr-1.5 fill-black"/> Advice
                </h3>
                <p className="text-sm font-mono text-gray-600 italic">{card.main_advisory_text}</p>
              </div>
              
              {/* Gap & Action Analysis */}
              <div>
                <h3 className="text-[12px] font-bold uppercase text-secondary mb-3 mt-5 flex items-center tracking-widest">
                  <AlertTriangle className="w-3 h-3 mr-1.5"/> Skill Gaps
                </h3>
                <div className="flex flex-wrap gap-1.5 mb-6">
                  {card.user_skill_gaps?.length > 0 ? card.user_skill_gaps.map(gap => (
                    <span key={gap} className="px-2.5 py-1 bg-red-50 text-red-700 text-[11px] font-bold rounded-md border border-red-100 uppercase tracking-tight">
                      {gap}
                    </span>
                  )) : <span className="text-green-600 text-sm font-medium">Paradigm alignment verified.</span>}
                </div>

                <h3 className="text-[12px] font-bold uppercase text-secondary mb-3 flex items-center tracking-widest">
                  <CheckCircle className="w-3 h-3 mr-1.5"/> Execution Path
                </h3>
                <ul className="space-y-3">
                  {card.actionable_path?.map((step, idx) => (
                    <li key={idx} className="text-sm text-gray-700 flex items-start leading-tight">
                      <span className="mr-3 font-mono text-gray-300 font-bold">{idx+1}</span> 
                      {step}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </Card>
        ))}
        
        {/* Empty State */}
        {!results && !loading && (
          <div className="py-20 text-center border-2 border-dashed border-gray-200 rounded-3xl">
            <p className="text-gray-400 font-medium">Input parameters to query the Search Engine.</p>
          </div>
        )}
      </div>
    </div>
  );
}