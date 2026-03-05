import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import { Card } from "../components/UI";
import { Cpu } from "lucide-react";
import API from "../services/api";

import ProfileStep from "../components/onboarding/ProfileStep";
import ProfileDetailsStep from "../components/onboarding/ProfileDetailStep";
import PersonalityStep from "../components/onboarding/PersonalityStep";
import ReviewStep from "../components/onboarding/ReviewStep";

export default function Ingest() {
  const { login, setLoading, loading } = useAuth();
  const navigate = useNavigate();

  const [step, setStep] = useState(1);
  const [questions, setQuestions] = useState([]);

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

  // -------- Fetch Personality Questions --------
  useEffect(() => {
    if (step === 3) {
      API.get("/personality/questions")
        .then((res) => setQuestions(res.data.questions))
        .catch((err) =>
          console.error("Failed to fetch personality questions:", err)
        );
    }
  }, [step]);

  // -------- Final Submit --------
  const handleFinalSubmit = async () => {
    setLoading(true);

    try {
      // 1️⃣ Evaluate personality
      const personaRes = await API.post(
        "/users/me/personality",
        { answers: formData.personality_answers }
      );

      // 2️⃣ Build final payload
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

      // 3️⃣ Register user
      const registerRes = await API.post(
        "/auth/register",
        finalPayload
      );

      // 4️⃣ Login + redirect
      login(registerRes.data.access_token);
      navigate("/");

    } catch (err) {
      console.error("Registration failed:", err);
      alert("Registration failed. Check console.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface px-4 py-12">
      <div className="w-full max-w-lg animate-fade-in">

        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-12 h-12 bg-black text-white rounded-xl flex items-center justify-center mx-auto mb-4 shadow-xl shadow-black/10">
            <Cpu size={20} />
          </div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Initialize Horizon.
          </h1>
          <p className="text-secondary text-sm mt-2">
            Construct your digital twin.
          </p>
        </div>

        <Card>

          {/* STEP 1 — Identity */}
          {step === 1 && (
            <ProfileStep
              formData={formData}
              setFormData={setFormData}
              next={() => setStep(2)}
            />
          )}

          {/* STEP 2 — Resume + Profile Details */}
          {step === 2 && (
            <ProfileDetailsStep
              formData={formData}
              setFormData={setFormData}
              next={() => setStep(3)}
              back={() => setStep(1)}
            />
          )}

          {/* STEP 3 — Personality */}
          {step === 3 && (
            <PersonalityStep
              questions={questions}
              formData={formData}
              setFormData={setFormData}
              next={() => setStep(4)}
              back={() => setStep(2)}
            />
          )}

          {/* STEP 4 — Review */}
          {step === 4 && (
            <ReviewStep
              formData={formData}
              handleFinalSubmit={handleFinalSubmit}
              back={() => setStep(3)}
              loading={loading}
            />
          )}

        </Card>
      </div>
    </div>
  );
}