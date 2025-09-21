import React, { useState } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';
import { 
  Target, 
  RotateCcw,
  Maximize2,
  Minimize2,
  ExternalLink,
  Sparkles,
  X,
  Loader2
} from 'lucide-react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';

interface Opportunity {
  title: string;
  url?: string;
  snippet?: string;
  source_type?: string;
  provenance: string[];
  confidence: number;
}

interface Stage {
  id: string;
  name: string;
  description?: string;
  eta_months?: number;
  nsqf_level?: number;
  skill_requirements: string[];
  top_opportunities: Opportunity[];
  provenance: string[];
}

interface PathBranch {
  id: string;
  title: string;
  summary: string;
  fit_score: number;
  confidence: number;
  stages: Stage[];
}

interface CareerTree {
  user_id: string;
  generated_at: string;
  domain_focus: string[];
  paths: PathBranch[];
  provenance: string[];
  confidence: number;
}

const CareerTreePage: React.FC = () => {
  const [careerTree, setCareerTree] = useState<CareerTree | null>(null);
  const [selectedPath, setSelectedPath] = useState<PathBranch | null>(null);
  const [selectedStage, setSelectedStage] = useState<Stage | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const generateCareerTree = async () => {
    setIsGenerating(true);
    try {
      const response = await axios.post('http://127.0.0.1:8000/careertree/generate/x');
      
      // The API returns { user_id, status, tree } structure
      if (response.data.status === 'ok' && response.data.tree) {
        setCareerTree(response.data.tree);
        if (response.data.tree.paths && response.data.tree.paths.length > 0) {
          setSelectedPath(response.data.tree.paths[0]);
        }
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (error) {
      console.error('Error generating career tree:', error);
      if (axios.isAxiosError(error)) {
        alert(`Failed to generate career tree: ${error.response?.data?.detail || error.message}`);
      } else {
        alert('Failed to generate career tree. Please try again.');
      }
    } finally {
      setIsGenerating(false);
    }
  };



  const getStageColor = (stageIndex: number, pathIndex: number) => {
    const baseColors = [
      'from-blue-400 to-blue-600',
      'from-purple-400 to-purple-600',
      'from-green-400 to-green-600',
      'from-orange-400 to-orange-600',
      'from-indigo-400 to-indigo-600'
    ];
    return baseColors[pathIndex % baseColors.length];
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-400';
    if (confidence >= 0.8) return 'text-yellow-400';
    if (confidence >= 0.7) return 'text-orange-400';
    return 'text-red-400';
  };

  const getConfidenceBg = (confidence: number) => {
    if (confidence >= 0.9) return 'bg-green-500/20';
    if (confidence >= 0.8) return 'bg-yellow-500/20';
    if (confidence >= 0.7) return 'bg-orange-500/20';
    return 'bg-red-500/20';
  };

  const filteredPaths = careerTree?.paths || [];

  return (
    <div className={`min-h-screen pt-32 pb-20 ${isFullscreen ? 'fixed inset-0 z-50 bg-horizon-950' : ''}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">
              Career <span className="gradient-text">Tree</span>
            </h1>
            <p className="text-xl text-white/70">
              Visualize your professional growth journey
            </p>
          </div>
          
          {/* <div className="flex items-center space-x-4">
            {!careerTree && (
              <Button
                onClick={generateCareerTree}
                loading={isGenerating}
                icon={isGenerating ? <Loader2 size={20} className="animate-spin" /> : <Sparkles size={20} />}
                size="lg"
              >
                {isGenerating ? 'Generating...' : 'Generate Career Tree'}
              </Button>
            )}
            <Button
              variant="ghost"
              onClick={() => setIsFullscreen(!isFullscreen)}
              icon={isFullscreen ? <Minimize2 size={20} /> : <Maximize2 size={20} />}
            >
              {isFullscreen ? 'Exit' : 'Fullscreen'}
            </Button>
          </div> */}
        </div>

        {!careerTree ? (
          /* Generate Tree State */
          <div className="flex items-center justify-center min-h-[60vh]">
            <Card variant="liquid" className="p-12 text-center max-w-md">
              <div className="w-20 h-20 bg-gradient-to-br from-horizon-800 to-horizon-900 border border-white/20 rounded-3xl flex items-center justify-center mx-auto mb-6">
                <Sparkles size={40} className="text-white" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-4">
                Generate Your Career Tree
              </h2>
              <p className="text-white/70 mb-8">
                Click the button above to generate a personalized career tree based on your profile and industry insights.
              </p>
              <Button
                onClick={generateCareerTree}
                loading={isGenerating}
                icon={isGenerating ? <Loader2 size={20} className="animate-spin" /> : <Sparkles size={20} />}
                size="lg"
              >
                {isGenerating ? 'Generating...' : 'Generate Career Tree'}
              </Button>
            </Card>
          </div>
        ) : (
          /* Tree Visualization */
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Tree View - Takes 60% of space */}
            <div className="lg:col-span-2">
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-2xl font-bold text-white">
                    Your Career Paths
                  </h2>
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      icon={<RotateCcw size={16} />}
                    >
                      Reset View
                    </Button>
                  </div>
                </div>

                {/* Tree Visualization */}
                <div className="relative min-h-[600px] overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-br from-horizon-900/50 to-horizon-800/50 rounded-3xl" />
                  
                  {/* Tree Container */}
                  <div className="relative p-8 h-full">
                    {filteredPaths.map((path, pathIndex) => (
                      <motion.div
                        key={path.id}
                        initial={{ opacity: 0, y: 50 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6, delay: pathIndex * 0.2 }}
                        className={`mb-12 ${selectedPath?.id === path.id ? 'z-10' : ''}`}
                      >
                        {/* Path Branch */}
                        <motion.div
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                          onClick={() => setSelectedPath(path)}
                          className={`relative cursor-pointer transition-all duration-300 ${
                            selectedPath?.id === path.id ? 'scale-105' : ''
                          }`}
                        >
                          {/* Path Line */}
                          <div className="absolute left-0 top-1/2 w-full h-1 bg-gradient-to-r from-white/20 to-transparent rounded-full" />
                          
                          {/* Path Node */}
                          <Card
                            variant="liquid"
                            className={`p-6 ml-8 ${
                              selectedPath?.id === path.id
                                ? 'ring-2 ring-blue-400/50 bg-gradient-to-br from-white/15 to-white/5'
                                : 'hover:bg-white/10'
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex-1">
                                <div className="flex items-center space-x-3 mb-2">
                                  <h3 className="text-xl font-bold text-white">
                                    {path.title}
                                  </h3>
                                  <div className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceBg(path.confidence)} ${getConfidenceColor(path.confidence)}`}>
                                    {Math.round(path.confidence * 100)}% confidence
                                  </div>
                                </div>
                                <p className="text-white/70 text-sm mb-3">
                                  {path.summary}
                                </p>
                                <div className="flex items-center space-x-4 text-xs text-white/60">
                                  <span>{path.stages.length} stages</span>
                                  <span>•</span>
                                  <span>{Math.round(path.fit_score * 100)}% fit</span>
                                </div>
                              </div>
                              <div className="w-12 h-12 bg-gradient-to-br from-horizon-800 to-horizon-900 border border-white/20 rounded-2xl flex items-center justify-center">
                                <span className="text-white font-bold text-lg">
                                  {pathIndex + 1}
                                </span>
                              </div>
                            </div>
                          </Card>

                          {/* Stages */}
                          <div className="ml-16 mt-6 space-y-4">
                            {path.stages.map((stage, stageIndex) => (
                              <motion.div
                                key={stage.id}
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ duration: 0.4, delay: stageIndex * 0.1 }}
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={() => setSelectedStage(stage)}
                                className={`relative cursor-pointer transition-all duration-300 ${
                                  selectedStage?.id === stage.id ? 'scale-110 z-20' : ''
                                }`}
                              >
                                {/* Stage Line */}
                                <div className="absolute left-0 top-1/2 w-8 h-0.5 bg-gradient-to-r from-white/30 to-transparent rounded-full" />
                                
                                {/* Stage Node */}
                                <Card
                                  variant="glass"
                                  className={`p-4 ml-8 ${
                                    selectedStage?.id === stage.id
                                      ? 'ring-2 ring-blue-400/50 bg-gradient-to-br from-white/15 to-white/5'
                                      : 'hover:bg-white/10'
                                  }`}
                                >
                                  <div className="flex items-center justify-between">
                                    <div className="flex-1">
                                      <h4 className="font-semibold text-white mb-1">
                                        {stage.name}
                                      </h4>
                                      <p className="text-white/60 text-sm mb-2">
                                        {stage.description}
                                      </p>
                                      <div className="flex items-center space-x-3 text-xs text-white/50">
                                        {stage.eta_months && (
                                          <span>{stage.eta_months} months</span>
                                        )}
                                        <span>•</span>
                                        <span>{stage.top_opportunities.length} opportunities</span>
                                        <span>•</span>
                                        <span>{stage.skill_requirements.length} skills</span>
                                      </div>
                                    </div>
                                    <div className={`w-8 h-8 rounded-xl bg-gradient-to-br ${getStageColor(stageIndex, pathIndex)} flex items-center justify-center`}>
                                      <span className="text-white font-bold text-sm">
                                        {stageIndex + 1}
                                      </span>
                                    </div>
                                  </div>
                                </Card>
                              </motion.div>
                            ))}
                          </div>
                        </motion.div>
                      </motion.div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Opportunities Panel - Takes 40% of space */}
            <div className="space-y-6">
              {selectedStage ? (
                /* Stage Details */
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="space-y-6"
                >
                  <div className="flex items-center justify-between">
                    <h3 className="text-xl font-bold text-white">
                      {selectedStage.name}
                    </h3>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedStage(null)}
                      icon={<X size={16} />}
                    >
                      Close
                    </Button>
                  </div>

                  <Card variant="glass" className="p-6">
                    <div className="space-y-4">
                      <div>
                        <h4 className="font-semibold text-white mb-2">Description</h4>
                        <p className="text-white/70 text-sm">
                          {selectedStage.description || 'No description available'}
                        </p>
                      </div>

                      {selectedStage.eta_months && (
                        <div>
                          <h4 className="font-semibold text-white mb-2">Duration</h4>
                          <p className="text-white/70 text-sm">
                            {selectedStage.eta_months} months
                          </p>
                        </div>
                      )}

                      <div>
                        <h4 className="font-semibold text-white mb-2">Required Skills</h4>
                        <div className="flex flex-wrap gap-2">
                          {selectedStage.skill_requirements.map((skill) => (
                            <span
                              key={skill}
                              className="px-2 py-1 bg-white/10 text-white/70 text-xs rounded"
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </Card>

                  <div>
                    <h4 className="text-lg font-semibold text-white mb-4">
                      Opportunities ({selectedStage.top_opportunities.length})
                    </h4>
                    <div className="space-y-3">
                      {selectedStage.top_opportunities.map((opportunity, index) => (
                        <motion.div
                          key={index}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.3, delay: index * 0.1 }}
                        >
                          <Card variant="glass" className="p-4 hover:scale-105 transition-all duration-300">
                            <div className="space-y-3">
                              <div className="flex items-start justify-between">
                                <h5 className="font-semibold text-white text-sm">
                                  {opportunity.title}
                                </h5>
                                <div className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceBg(opportunity.confidence)} ${getConfidenceColor(opportunity.confidence)}`}>
                                  {Math.round(opportunity.confidence * 100)}%
                                </div>
                              </div>
                              
                              {opportunity.snippet && (
                                <p className="text-white/70 text-xs">
                                  {opportunity.snippet}
                                </p>
                              )}

                              <div className="flex items-center justify-between">
                                <span className="text-white/50 text-xs">
                                  {opportunity.source_type || 'Unknown source'}
                                </span>
                                {opportunity.url && (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => window.open(opportunity.url, '_blank')}
                                    icon={<ExternalLink size={12} />}
                                  >
                                    Apply
                                  </Button>
                                )}
                              </div>
                            </div>
                          </Card>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                </motion.div>
              ) : (
                /* Default State */
                <Card variant="glass" className="p-8 text-center">
                  <div className="w-16 h-16 bg-white/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <Target size={32} className="text-white/50" />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">
                    Select a Stage
                  </h3>
                  <p className="text-white/70 text-sm">
                    Click on any stage in the career tree to view available opportunities and details.
                  </p>
                </Card>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CareerTreePage;
