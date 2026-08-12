import { useState, useEffect, useRef } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import { Cpu, UploadCloud } from "lucide-react";
import API from "../services/api";
import { toast } from "sonner";

export default function Ingest() {
  const { login, setLoading, loading, email } = useAuth();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (email === 'demo@horizon.com') {
      navigate('/discover');
      toast.error("Profile ingestion is disabled in demo mode.");
    }
  }, [email, navigate]);

  const [questions, setQuestions] = useState([]);
  const [resumeUploading, setResumeUploading] = useState(false);
  const [resumeUploaded, setResumeUploaded] = useState(false);

  const [formData, setFormData] = useState({
    email: "",
    password: "",
    profile: {
      name: "",
      phone: "",
      linkedin_link: "",
      github_link: "",
      preferences: {
        role: "",
        location: ""
      },
      skills: [],
      education: [],
      projects: []
    },
    personality_answers: []
  });

  useEffect(() => {
    API.get("/personality/questions")
      .then((res) => {
        setQuestions(res.data.questions);
        // Initialize personality answers
        setFormData(prev => ({
          ...prev,
          personality_answers: res.data.questions.map(q => ({
            question_id: q.id,
            answer_value: 3
          }))
        }));
      })
      .catch((err) => console.error("Failed to fetch personality questions:", err));
  }, []);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setResumeUploading(true);
    const formDataPayload = new FormData();
    formDataPayload.append("file", file);

    try {
      const res = await API.post("/auth/parse_resume", formDataPayload, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      const parsedProfile = res.data;
      
      setFormData((prev) => ({
        ...prev,
        profile: {
          ...prev.profile,
          ...parsedProfile,
          preferences: {
            ...prev.profile.preferences,
            ...(parsedProfile.preferences || {})
          }
        }
      }));
      setResumeUploaded(true);
      toast.success("Resume parsed successfully!");
    } catch (err) {
      console.error(err);
      toast.error("Failed to parse resume.");
    } finally {
      setResumeUploading(false);
    }
  };

  const handlePreferenceChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      profile: {
        ...prev.profile,
        preferences: {
          ...prev.profile.preferences,
          [field]: value
        }
      }
    }));
  };

  const handleAnswerChange = (questionId, value) => {
    setFormData((prev) => ({
      ...prev,
      personality_answers: prev.personality_answers.map(ans => 
        ans.question_id === questionId ? { ...ans, answer_value: value } : ans
      )
    }));
  };

  const handleFinalSubmit = async () => {
    setLoading(true);

    try {
      const personaRes = await API.post(
        "/users/me/personality",
        { answers: formData.personality_answers }
      );

      const finalPayload = {
        email: formData.email,
        password: formData.password,
        profile: formData.profile,
        personality: {
          completed: true,
          scores: personaRes.data.scores,
          type: personaRes.data.persona
        }
      };

      const registerRes = await API.post(
        "/auth/register",
        finalPayload
      );

      login(registerRes.data.access_token);
      navigate("/");

    } catch (err) {
      console.error("Registration failed:", err);
      toast.error("Registration failed. Check console.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface px-4 py-24">
      <div className="w-full max-w-2xl mx-auto animate-fade-in space-y-12">
        <div className="text-center">
          <div className="w-12 h-12 bg-black text-white rounded-xl flex items-center justify-center mx-auto mb-4 shadow-xl shadow-black/10">
            <Cpu size={20} />
          </div>
          <h1 className="text-3xl font-bold tracking-tight">
            Initialize Horizon.
          </h1>
          <p className="text-neutral-500 mt-2">
            Construct your digital twin.
          </p>
        </div>

        <div className="space-y-10">
          {/* Credentials Section */}
          <div className="bg-white p-8 rounded-3xl shadow-sm border border-neutral-200/60">
            <h2 className="text-xl font-bold mb-4">Account Credentials</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-neutral-700 mb-1">Email</label>
                <input 
                  type="email" 
                  value={formData.email} 
                  onChange={(e) => setFormData({...formData, email: e.target.value})} 
                  className="w-full px-4 py-2.5 rounded-xl border border-neutral-300 focus:border-neutral-950 focus:ring-1 focus:ring-neutral-950 outline-none transition-all"
                  placeholder="name@example.com"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-neutral-700 mb-1">Password</label>
                <input 
                  type="password" 
                  value={formData.password} 
                  onChange={(e) => setFormData({...formData, password: e.target.value})} 
                  className="w-full px-4 py-2.5 rounded-xl border border-neutral-300 focus:border-neutral-950 focus:ring-1 focus:ring-neutral-950 outline-none transition-all"
                  placeholder="••••••••"
                />
              </div>
            </div>
          </div>

          {/* Resume Upload Section */}
          <div className="bg-white p-8 rounded-3xl shadow-sm border border-neutral-200/60">
            <h2 className="text-xl font-bold mb-4">Upload Resume</h2>
            <div 
              className="border-2 border-dashed border-neutral-300 rounded-2xl p-8 text-center hover:border-neutral-950 hover:bg-neutral-50 transition-all cursor-pointer"
              onClick={() => fileInputRef.current?.click()}
            >
              <UploadCloud className="mx-auto text-neutral-400 mb-3" size={32} />
              <p className="text-sm font-medium text-neutral-700">
                {resumeUploading ? "Parsing resume..." : resumeUploaded ? "Resume uploaded successfully! Click to replace." : "Click or drag PDF to upload"}
              </p>
              <input 
                type="file" 
                ref={fileInputRef} 
                onChange={handleFileUpload} 
                className="hidden" 
                accept=".pdf"
              />
            </div>
          </div>

          {/* Preferences Section */}
          <div className="bg-white p-8 rounded-3xl shadow-sm border border-neutral-200/60">
            <h2 className="text-xl font-bold mb-4">Target Preferences</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-neutral-700 mb-1">Target Role</label>
                <input 
                  type="text" 
                  value={formData.profile.preferences.role} 
                  onChange={(e) => handlePreferenceChange('role', e.target.value)} 
                  className="w-full px-4 py-2.5 rounded-xl border border-neutral-300 focus:border-neutral-950 focus:ring-1 focus:ring-neutral-950 outline-none transition-all"
                  placeholder="e.g. Senior Software Engineer"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-neutral-700 mb-1">Target Location</label>
                <input 
                  type="text" 
                  value={formData.profile.preferences.location} 
                  onChange={(e) => handlePreferenceChange('location', e.target.value)} 
                  className="w-full px-4 py-2.5 rounded-xl border border-neutral-300 focus:border-neutral-950 focus:ring-1 focus:ring-neutral-950 outline-none transition-all"
                  placeholder="e.g. San Francisco, CA"
                />
              </div>
            </div>
          </div>

          {/* Personality Quiz Section */}
          <div className="bg-white p-8 rounded-3xl shadow-sm border border-neutral-200/60">
            <h2 className="text-xl font-bold mb-2">Personality Assessment</h2>
            <p className="text-sm text-neutral-500 mb-6">Answer intuitively. This shapes your agent's negotiation style.</p>
            
            <div className="space-y-8">
              {questions.map((q) => {
                const answer = formData.personality_answers.find(a => a.question_id === q.id);
                const value = answer ? answer.answer_value : 3;

                return (
                  <div key={q.id}>
                    <p className="text-sm font-semibold text-neutral-800 mb-4">{q.text}</p>
                    <div className="flex items-center justify-between gap-4">
                      <span className="text-xs font-medium text-neutral-500 w-16 text-right">Disagree</span>
                      <div className="flex-1 flex justify-between px-2">
                        {[1, 2, 3, 4, 5].map((val) => (
                          <button
                            key={val}
                            onClick={() => handleAnswerChange(q.id, val)}
                            className={`w-8 h-8 rounded-full border-2 transition-all ${
                              value === val 
                                ? 'border-neutral-950 bg-neutral-950 text-white' 
                                : 'border-neutral-300 text-transparent hover:border-neutral-400'
                            }`}
                          />
                        ))}
                      </div>
                      <span className="text-xs font-medium text-neutral-500 w-16">Agree</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Submit Action */}
          <div className="pt-4">
            <button 
              onClick={handleFinalSubmit}
              disabled={loading}
              className="w-full py-4 rounded-xl bg-black text-white font-bold text-lg hover:bg-neutral-800 transition-all shadow-md disabled:opacity-70 flex items-center justify-center gap-2"
            >
              {loading ? (
                <span className="animate-pulse">Initializing...</span>
              ) : (
                <>
                  Initialize <Cpu size={20} />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}