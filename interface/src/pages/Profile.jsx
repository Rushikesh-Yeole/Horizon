import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import { toast } from 'sonner';
import { User, Plus, X, Sparkles, Check, Github, Linkedin, Briefcase, MapPin, Code2, GraduationCap, Cpu } from 'lucide-react';

const SKILL_PRESETS = [
  'PyTorch', 'CUDA', 'Neo4j', 'FastAPI', 'Distributed Systems', 
  'Graph RAG', 'Rust', 'LLM Orchestration', 'LangChain', 'QLoRA'
];

export default function Profile() {
  const queryClient = useQueryClient();
  
  // Profile form state
  const [name, setName] = useState('');
  const [role, setRole] = useState('');
  const [location, setLocation] = useState('');
  const [githubLink, setGithubLink] = useState('');
  const [linkedinLink, setLinkedinLink] = useState('');
  const [phone, setPhone] = useState('');
  const [skills, setSkills] = useState([]);
  const [newSkill, setNewSkill] = useState('');
  const [education, setEducation] = useState([]);
  const [projects, setProjects] = useState([]);

  const { data: userData, isLoading } = useQuery({
    queryKey: ['user', 'me'],
    queryFn: async () => {
      const res = await api.get('/users/me');
      return res.data;
    }
  });

  const user = userData?.user;

  useEffect(() => {
    if (user && user.profile) {
      const p = user.profile;
      setName(p.name || user.email?.split('@')[0] || '');
      setRole(p.role || p.preferences?.role || '');
      setLocation(p.location || p.preferences?.location || '');
      setGithubLink(p.github_link || '');
      setLinkedinLink(p.linkedin_link || '');
      setPhone(p.phone || '');
      setSkills(p.skills || []);
      setEducation(p.education || []);
      setProjects(p.projects || []);
    }
  }, [user]);

  const updateProfileMutation = useMutation({
    mutationFn: async (updatedProfile) => {
      const res = await api.put('/users/me/profile', updatedProfile);
      return res.data;
    },
    onSuccess: () => {
      toast.success('Profile & graph calibration updated');
      queryClient.invalidateQueries({ queryKey: ['user', 'me'] });
    },
    onError: () => {
      toast.error('Failed to update profile');
    }
  });

  const handleSave = () => {
    const updatedProfile = {
      ...user?.profile,
      name,
      phone,
      github_link: githubLink,
      linkedin_link: linkedinLink,
      preferences: {
        ...user?.profile?.preferences,
        role,
        location
      },
      skills,
      education,
      projects
    };
    updateProfileMutation.mutate(updatedProfile);
  };

  const addSkill = (skillToAdd) => {
    const val = (skillToAdd || newSkill).trim();
    if (val && !skills.includes(val)) {
      setSkills([...skills, val]);
      if (!skillToAdd) setNewSkill('');
    }
  };

  const removeSkill = (skillToRemove) => {
    setSkills(skills.filter(s => s !== skillToRemove));
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-white pt-28 pb-20 px-6 max-w-4xl mx-auto flex items-center justify-center">
        <div className="flex items-center gap-3 text-neutral-500 font-mono text-sm">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
          Loading Profile Engine...
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white pt-24 sm:pt-28 pb-20 px-4 sm:px-8 lg:px-12 xl:px-16 max-w-[1680px] w-full mx-auto">
      {/* 1. Executive Hero Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 pb-8 border-b border-neutral-200/80 mb-10">
        <div className="flex items-center gap-5">
          <div className="relative w-16 h-16 rounded-full bg-neutral-950 text-white flex items-center justify-center border border-neutral-300 shadow-md shrink-0 overflow-hidden">
            {user?.avatar_url ? (
              <img 
                src={`${api.defaults.baseURL}${user.avatar_url}`} 
                alt="Avatar" 
                className="w-full h-full object-cover"
              />
            ) : (
              <User size={28} className="stroke-[1.8]" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-neutral-950">
                {name || 'Alex Chen'}
              </h1>
            </div>
            <p className="text-xs font-mono text-neutral-500 mt-1 flex items-center gap-2">
              <span>{user?.email}</span>
              <span>•</span>
              <span className="text-neutral-800 font-semibold">{role || 'AI Engineer'}</span>
            </p>
          </div>
        </div>

        <button
          onClick={handleSave}
          disabled={updateProfileMutation.isPending}
          className="px-6 py-2.5 rounded-full bg-neutral-950 text-white font-semibold text-xs hover:bg-neutral-800 transition-all shadow-sm disabled:opacity-50 flex items-center justify-center gap-2 self-start sm:self-auto shrink-0 cursor-pointer"
        >
          {updateProfileMutation.isPending ? (
            'Saving Profile...'
          ) : (
            <>
              <Check size={14} />
              Save Profile Changes
            </>
          )}
        </button>
      </div>

      {/* 2. Main Studio Grid (2-Column Studio on Laptop, Single Column on Mobile) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Left Column: Career Targets & Social Profiles */}
        <div className="lg:col-span-4 space-y-8">
          {/* Target Preferences Section */}
          <div className="bg-neutral-50/50 rounded-3xl p-6 sm:p-7 border border-neutral-200/80 shadow-2xs">
            <div className="flex items-center gap-2.5 mb-6">
              <div className="p-2 rounded-xl bg-neutral-950 text-white">
                <Briefcase size={16} />
              </div>
              <div>
                <h3 className="text-base font-extrabold text-neutral-950 tracking-tight">Career Targets & Positioning</h3>
                <p className="text-xs text-neutral-500 font-mono">Market discovery alignment</p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-mono font-bold text-neutral-600 mb-1.5 uppercase">Full Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Alex Chen"
                  className="w-full px-4 py-2.5 rounded-xl border border-neutral-200 bg-white text-xs font-medium focus:border-neutral-950 focus:outline-none transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-mono font-bold text-neutral-600 mb-1.5 uppercase">Target Role Title</label>
                <input
                  type="text"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  placeholder="e.g. AI Research Engineer"
                  className="w-full px-4 py-2.5 rounded-xl border border-neutral-200 bg-white text-xs font-medium focus:border-neutral-950 focus:outline-none transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-mono font-bold text-neutral-600 mb-1.5 uppercase">Target Location</label>
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="e.g. San Francisco / Remote"
                  className="w-full px-4 py-2.5 rounded-xl border border-neutral-200 bg-white text-xs font-medium focus:border-neutral-950 focus:outline-none transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-mono font-bold text-neutral-600 mb-1.5 uppercase">Phone / Contact</label>
                <input
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+1 (555) 019-2834"
                  className="w-full px-4 py-2.5 rounded-xl border border-neutral-200 bg-white text-xs font-medium focus:border-neutral-950 focus:outline-none transition-all"
                />
              </div>
            </div>
          </div>

          {/* Links & Social Integration */}
          <div className="bg-neutral-50/50 rounded-3xl p-6 sm:p-7 border border-neutral-200/80 shadow-2xs">
            <div className="flex items-center gap-2.5 mb-6">
              <div className="p-2 rounded-xl bg-neutral-950 text-white">
                <Github size={16} />
              </div>
              <div>
                <h3 className="text-base font-extrabold text-neutral-950 tracking-tight">Public Profiles & Links</h3>
                <p className="text-xs text-neutral-500 font-mono">Proof of work validation</p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-mono font-bold text-neutral-600 mb-1.5 uppercase">GitHub Profile URL</label>
                <input
                  type="text"
                  value={githubLink}
                  onChange={(e) => setGithubLink(e.target.value)}
                  placeholder="https://github.com/alexchen"
                  className="w-full px-4 py-2.5 rounded-xl border border-neutral-200 bg-white text-xs font-mono focus:border-neutral-950 focus:outline-none transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-mono font-bold text-neutral-600 mb-1.5 uppercase">LinkedIn Profile URL</label>
                <input
                  type="text"
                  value={linkedinLink}
                  onChange={(e) => setLinkedinLink(e.target.value)}
                  placeholder="https://linkedin.com/in/alexchen"
                  className="w-full px-4 py-2.5 rounded-xl border border-neutral-200 bg-white text-xs font-mono focus:border-neutral-950 focus:outline-none transition-all"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Skills, Projects, and Education */}
        <div className="lg:col-span-8 space-y-8">
          
          {/* Skill Matrix Section */}
          <div className="bg-neutral-50/50 rounded-3xl p-6 sm:p-7 border border-neutral-200/80 shadow-2xs">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-neutral-950 text-white">
                  <Code2 size={16} />
                </div>
                <div>
                  <h3 className="text-base font-extrabold text-neutral-950 tracking-tight">Skill Matrix & Competencies</h3>
                </div>
              </div>
              <span className="text-xs font-mono text-neutral-500 font-semibold">{skills.length} Active</span>
            </div>

            {/* Active Skills Tag Cloud */}
            <div className="flex flex-wrap gap-2 mb-5 min-h-[42px] p-3 rounded-2xl bg-white border border-neutral-200/70">
              {skills.length === 0 ? (
                <p className="text-xs text-neutral-400 font-mono italic self-center">No skills added yet. Add custom skills below or select from presets.</p>
              ) : (
                skills.map((skill) => (
                  <span 
                    key={skill} 
                    className="px-3 py-1 rounded-full bg-neutral-100 border border-neutral-200 text-neutral-900 font-mono text-xs font-medium flex items-center gap-2 hover:border-neutral-400 transition-all group"
                  >
                    {skill}
                    <button 
                      onClick={() => removeSkill(skill)}
                      className="text-neutral-400 hover:text-rose-600 transition-colors cursor-pointer"
                    >
                      <X size={12} />
                    </button>
                  </span>
                ))
              )}
            </div>

            {/* Input & Preset Bar */}
            <div className="space-y-3">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newSkill}
                  onChange={(e) => setNewSkill(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addSkill()}
                  placeholder="Type a skill (e.g. PyTorch, CUDA, Neo4j) and press Enter..."
                  className="flex-1 px-4 py-2.5 rounded-xl border border-neutral-200 bg-white text-xs font-mono focus:border-neutral-950 focus:outline-none transition-all"
                />
                <button
                  onClick={() => addSkill()}
                  className="px-4 py-2.5 rounded-xl bg-neutral-950 text-white font-semibold text-xs hover:bg-neutral-800 transition-all flex items-center gap-1.5 shrink-0 cursor-pointer"
                >
                  <Plus size={14} />
                  Add Skill
                </button>
              </div>

              {/* Presets */}
              <div className="flex items-center gap-1.5 flex-wrap pt-1">
                <span className="text-[10px] font-mono text-neutral-400 font-semibold uppercase mr-1">Quick Add:</span>
                {SKILL_PRESETS.map((preset) => {
                  const isSelected = skills.includes(preset);
                  return (
                    <button
                      key={preset}
                      onClick={() => addSkill(preset)}
                      disabled={isSelected}
                      className={`text-[11px] font-mono px-2.5 py-1 rounded-lg border transition-all cursor-pointer ${
                        isSelected
                          ? 'bg-neutral-100 text-neutral-400 border-neutral-200 cursor-default opacity-60'
                          : 'bg-white text-neutral-700 border-neutral-200 hover:border-neutral-950 hover:bg-neutral-50'
                      }`}
                    >
                      + {preset}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Projects Section */}
          <div className="bg-neutral-50/50 rounded-3xl p-6 sm:p-7 border border-neutral-200/80 shadow-2xs">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-neutral-950 text-white">
                  <Briefcase size={16} />
                </div>
                <div>
                  <h3 className="text-base font-extrabold text-neutral-950 tracking-tight">Key Projects & Artifacts</h3>
                  <p className="text-xs text-neutral-500 font-mono">Proof of technical execution</p>
                </div>
              </div>
              <button 
                onClick={() => setProjects([...projects, { title: '', desc: '' }])}
                className="px-3 py-1.5 rounded-lg border border-neutral-200 bg-white text-xs font-semibold hover:border-neutral-950 transition-all flex items-center gap-1 cursor-pointer"
              >
                <Plus size={14} /> Add Project
              </button>
            </div>
            
            <div className="space-y-4">
              {projects.length === 0 ? (
                <p className="text-xs text-neutral-400 font-mono italic text-center py-4">No projects added.</p>
              ) : (
                projects.map((proj, idx) => (
                  <div key={idx} className="p-4 rounded-2xl bg-white border border-neutral-200 relative group">
                    <button 
                      onClick={() => setProjects(projects.filter((_, i) => i !== idx))}
                      className="absolute top-4 right-4 text-neutral-400 hover:text-rose-500 transition-colors opacity-0 group-hover:opacity-100 cursor-pointer"
                    >
                      <X size={16} />
                    </button>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-[10px] font-mono font-bold text-neutral-500 mb-1 uppercase">Project Title</label>
                        <input 
                          type="text" 
                          value={proj.title || ''} 
                          onChange={(e) => {
                            const newProj = [...projects];
                            newProj[idx].title = e.target.value;
                            setProjects(newProj);
                          }}
                          placeholder="e.g. Distributed Graph Database"
                          className="w-full px-3 py-2 rounded-lg border border-neutral-200 bg-neutral-50 text-xs font-semibold focus:border-neutral-950 focus:bg-white focus:outline-none transition-all"
                        />
                      </div>
                      <div>
                        <label className="block text-[10px] font-mono font-bold text-neutral-500 mb-1 uppercase">Description</label>
                        <textarea 
                          value={proj.desc || ''} 
                          onChange={(e) => {
                            const newProj = [...projects];
                            newProj[idx].desc = e.target.value;
                            setProjects(newProj);
                          }}
                          placeholder="Describe the technical implementation, impact, and scale..."
                          rows={3}
                          className="w-full px-3 py-2 rounded-lg border border-neutral-200 bg-neutral-50 text-xs focus:border-neutral-950 focus:bg-white focus:outline-none transition-all resize-none"
                        />
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Education Section */}
          <div className="bg-neutral-50/50 rounded-3xl p-6 sm:p-7 border border-neutral-200/80 shadow-2xs">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-neutral-950 text-white">
                  <GraduationCap size={16} />
                </div>
                <div>
                  <h3 className="text-base font-extrabold text-neutral-950 tracking-tight">Education</h3>
                  <p className="text-xs text-neutral-500 font-mono">Degrees, universities, and formal credentials</p>
                </div>
              </div>
              <button 
                onClick={() => setEducation([...education, { degree: '', branch: '', college: '' }])}
                className="px-3 py-1.5 rounded-lg border border-neutral-200 bg-white text-xs font-semibold hover:border-neutral-950 transition-all flex items-center gap-1 cursor-pointer"
              >
                <Plus size={14} /> Add Education
              </button>
            </div>
            
            <div className="space-y-4">
              {education.length === 0 ? (
                <p className="text-xs text-neutral-400 font-mono italic text-center py-4">No education entries added.</p>
              ) : (
                education.map((edu, idx) => (
                  <div key={idx} className="p-4 rounded-2xl bg-white border border-neutral-200 relative group">
                    <button 
                      onClick={() => setEducation(education.filter((_, i) => i !== idx))}
                      className="absolute top-4 right-4 text-neutral-400 hover:text-rose-500 transition-colors opacity-0 group-hover:opacity-100 cursor-pointer"
                    >
                      <X size={16} />
                    </button>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-[10px] font-mono font-bold text-neutral-500 mb-1 uppercase">Degree</label>
                        <input 
                          type="text" 
                          value={edu.degree || ''} 
                          onChange={(e) => {
                            const newEdu = [...education];
                            newEdu[idx].degree = e.target.value;
                            setEducation(newEdu);
                          }}
                          placeholder="e.g. B.S."
                          className="w-full px-3 py-2 rounded-lg border border-neutral-200 bg-neutral-50 text-xs focus:border-neutral-950 focus:bg-white focus:outline-none transition-all"
                        />
                      </div>
                      <div>
                        <label className="block text-[10px] font-mono font-bold text-neutral-500 mb-1 uppercase">Branch / Major</label>
                        <input 
                          type="text" 
                          value={edu.branch || ''} 
                          onChange={(e) => {
                            const newEdu = [...education];
                            newEdu[idx].branch = e.target.value;
                            setEducation(newEdu);
                          }}
                          placeholder="e.g. Computer Science"
                          className="w-full px-3 py-2 rounded-lg border border-neutral-200 bg-neutral-50 text-xs focus:border-neutral-950 focus:bg-white focus:outline-none transition-all"
                        />
                      </div>
                      <div className="sm:col-span-2">
                        <label className="block text-[10px] font-mono font-bold text-neutral-500 mb-1 uppercase">College / University</label>
                        <input 
                          type="text" 
                          value={edu.college || ''} 
                          onChange={(e) => {
                            const newEdu = [...education];
                            newEdu[idx].college = e.target.value;
                            setEducation(newEdu);
                          }}
                          placeholder="e.g. Stanford University"
                          className="w-full px-3 py-2 rounded-lg border border-neutral-200 bg-neutral-50 text-xs focus:border-neutral-950 focus:bg-white focus:outline-none transition-all"
                        />
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
