import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Upload, 
  FileText, 
  Brain, 
  CheckCircle, 
  ArrowRight, 
  ArrowLeft,
  Star,
  Target
} from 'lucide-react';
import axios from 'axios';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Card from '../components/ui/Card';
import ProgressBar from '../components/ui/ProgressBar';
import { getUserUrl, buildMainBackendUrl } from '../config/api';

interface MBTIQuestion {
  id: string;
  question: string;
  options: {
    text: string;
    value: 'E' | 'I' | 'S' | 'N' | 'T' | 'F' | 'J' | 'P';
  }[];
}

const ProfileSetupPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  const [mbtiQuestions, setMbtiQuestions] = useState<MBTIQuestion[]>([]);
  const [personalityScores, setPersonalityScores] = useState<{ [key: string]: number }>({});
  const [formData, setFormData] = useState({
    resume: null as File | null,
    education: '',
    experience: '',
    skills: [] as string[],
    interests: [] as string[],
    mbtiAnswers: {} as { [key: string]: string },
    // Registration data from previous step
    name: '',
    email: '',
    password: '',
    phone: '',
    linkedin: '',
    github: '',
    preferences: { location: '', role: '' },
    projects: [] as Array<{ title: string; desc: string }>,
  });

  const totalSteps = 4;
  const progress = (currentStep / totalSteps) * 100;

  // Load MBTI questions from backend
  useEffect(() => {
    const loadQuestions = async () => {
      try {
        const response = await axios.get(getUserUrl('QUESTIONS'));
        setMbtiQuestions(response.data.questions);
      } catch (error) {
        console.error('Error loading MBTI questions:', error);
        // Fallback to hardcoded questions if API fails
        setMbtiQuestions([
          {
            id: 'q1',
            question: 'At a party, you would rather:',
            options: [
              { text: 'Meet new people and socialize', value: 'E' },
              { text: 'Have deep conversations with a few close friends', value: 'I' },
            ],
          },
          {
            id: 'q2',
            question: 'When learning something new, you prefer:',
            options: [
              { text: 'Hands-on experience and practical examples', value: 'S' },
              { text: 'Understanding the big picture and concepts', value: 'N' },
            ],
          },
          {
            id: 'q3',
            question: 'When making decisions, you rely more on:',
            options: [
              { text: 'Logic and objective analysis', value: 'T' },
              { text: 'Values and how it affects people', value: 'F' },
            ],
          },
          {
            id: 'q4',
            question: 'You prefer to:',
            options: [
              { text: 'Plan ahead and stick to schedules', value: 'J' },
              { text: 'Keep your options open and be flexible', value: 'P' },
            ],
          },
          {
            id: 'q5',
            question: 'In group projects, you typically:',
            options: [
              { text: 'Take charge and organize the team', value: 'E' },
              { text: 'Contribute ideas and support others', value: 'I' },
            ],
          },
          {
            id: 'q6',
            question: 'You are more interested in:',
            options: [
              { text: 'What is real and practical', value: 'S' },
              { text: 'What is possible and theoretical', value: 'N' },
            ],
          },
        ]);
      }
    };

    loadQuestions();
  }, []);

  // Handle registration data from previous step
  useEffect(() => {
    if (location.state?.registrationData) {
      const { name, email, password } = location.state.registrationData;
      setFormData(prev => ({
        ...prev,
        name,
        email,
        password
      }));
    }
  }, [location.state]);


  const skillCategories = [
    { name: 'Programming', skills: ['JavaScript', 'Python', 'Java', 'C++', 'TypeScript', 'Go', 'Rust'] },
    { name: 'Web Development', skills: ['React', 'Vue.js', 'Angular', 'Node.js', 'Express', 'Django', 'Flask'] },
    { name: 'Data Science', skills: ['Machine Learning', 'Data Analysis', 'Statistics', 'R', 'SQL', 'Pandas', 'NumPy'] },
    { name: 'Design', skills: ['UI/UX Design', 'Figma', 'Adobe Creative Suite', 'Sketch', 'Prototyping', 'User Research'] },
    { name: 'Business', skills: ['Project Management', 'Marketing', 'Sales', 'Strategy', 'Finance', 'Operations'] },
  ];

  const interestDomains = [
    'Artificial Intelligence',
    'Web Development',
    'Mobile Development',
    'Data Science',
    'Cybersecurity',
    'Cloud Computing',
    'Blockchain',
    'Game Development',
    'UI/UX Design',
    'Product Management',
    'Digital Marketing',
    'DevOps',
  ];

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFormData(prev => ({ ...prev, resume: file }));
    }
  };

  const handleSkillToggle = (skill: string) => {
    setFormData(prev => ({
      ...prev,
      skills: prev.skills.includes(skill)
        ? prev.skills.filter(s => s !== skill)
        : [...prev.skills, skill]
    }));
  };

  const handleInterestToggle = (interest: string) => {
    setFormData(prev => ({
      ...prev,
      interests: prev.interests.includes(interest)
        ? prev.interests.filter(i => i !== interest)
        : [...prev.interests, interest]
    }));
  };

  const handleMBTIAnswer = (questionId: string, answer: string) => {
    setFormData(prev => ({
      ...prev,
      mbtiAnswers: { ...prev.mbtiAnswers, [questionId]: answer }
    }));
  };

  const nextStep = () => {
    if (currentStep < totalSteps) {
      setCurrentStep(prev => prev + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    
    try {
      let resumeData = null;
      
      // Upload resume if provided
      if (formData.resume) {
        const formDataResume = new FormData();
        formDataResume.append('file', formData.resume);
        
        const resumeResponse = await axios.post(getUserUrl('RESUME'), formDataResume, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        
        resumeData = resumeResponse.data;
      }

      // Process MBTI answers to get personality scores
      const answersArray = Object.entries(formData.mbtiAnswers).map(([questionId, answer]) => ({
        question_id: questionId,
        answer: answer
      }));

      const personalityResponse = await axios.post(getUserUrl('ANSWERS'), {
        answers: answersArray
      });

      const personalityScores = personalityResponse.data['personality scores'];

      // Prepare user data for registration
      const userData = {
        name: formData.name,
        email: formData.email,
        phone: formData.phone || '',
        linkedin: formData.linkedin || '',
        github: formData.github || '',
        preferences: formData.preferences,
        education: formData.education ? [{
          degree: formData.education,
          branch: '',
          college: ''
        }] : [],
        skills: formData.skills,
        projects: formData.projects,
        personality: personalityScores,
        bucket: resumeData?.bucket || null,
        destination_blob: resumeData?.dest_blob || null,
        password: formData.password
      };

      // Register user
      const registerResponse = await axios.post(buildMainBackendUrl('/user/register'), userData);
      
      // Store user ID and navigate to jobs
      localStorage.setItem('user_id', registerResponse.data.user_id);
      navigate('/jobs');
      
    } catch (error) {
      console.error('Profile setup error:', error);
      if (axios.isAxiosError(error)) {
        setErrors({ 
          general: error.response?.data?.message || 'Profile setup failed. Please try again.' 
        });
      } else {
        setErrors({ general: 'An unexpected error occurred. Please try again.' });
      }
    } finally {
      setLoading(false);
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return formData.resume || (formData.education && formData.experience);
      case 2:
        return formData.skills.length > 0;
      case 3:
        return formData.interests.length > 0;
      case 4:
        return Object.keys(formData.mbtiAnswers).length === mbtiQuestions.length;
      default:
        return false;
    }
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <motion.div
            key="step1"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div className="text-center mb-8">
              <div className="w-16 h-16 bg-gradient-to-br from-horizon-800 to-horizon-900 border border-white/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <FileText size={32} className="text-white" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">
                Upload Your Resume
              </h2>
              <p className="text-white/70">
                Upload your resume or fill in your details manually
              </p>
            </div>

            <div className="space-y-6">
              <div className="border-2 border-dashed border-white/20 rounded-xl p-8 text-center hover:border-white/40 transition-colors duration-300">
                <input
                  type="file"
                  accept=".pdf,.doc,.docx"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="resume-upload"
                />
                <label
                  htmlFor="resume-upload"
                  className="cursor-pointer flex flex-col items-center space-y-4"
                >
                  <Upload size={48} className="text-white/50" />
                  <div>
                    <p className="text-white font-medium">
                      {formData.resume ? formData.resume.name : 'Click to upload resume'}
                    </p>
                    <p className="text-white/50 text-sm">
                      PDF, DOC, or DOCX (max 10MB)
                    </p>
                  </div>
                </label>
              </div>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-white/10" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-horizon-900 text-white/70">Or fill manually</span>
                </div>
              </div>

              <Input
                label="Education"
                value={formData.education}
                onChange={(e) => setFormData(prev => ({ ...prev, education: e.target.value }))}
                placeholder="e.g., B.Tech Computer Science, IIT Delhi"
                variant="glass"
              />

              <Input
                label="Experience"
                value={formData.experience}
                onChange={(e) => setFormData(prev => ({ ...prev, experience: e.target.value }))}
                placeholder="e.g., 2 years as Software Engineer at Google"
                variant="glass"
              />
            </div>
          </motion.div>
        );

      case 2:
        return (
          <motion.div
            key="step2"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div className="text-center mb-8">
              <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Target size={32} className="text-white" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">
                Select Your Skills
              </h2>
              <p className="text-white/70">
                Choose the skills you have or want to develop
              </p>
            </div>

            <div className="space-y-6">
              {skillCategories.map((category) => (
                <div key={category.name}>
                  <h3 className="text-lg font-semibold text-white mb-3">
                    {category.name}
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {category.skills.map((skill) => (
                      <button
                        key={skill}
                        onClick={() => handleSkillToggle(skill)}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${
                          formData.skills.includes(skill)
                            ? 'bg-gradient-to-r from-horizon-800 to-horizon-900 text-white'
                            : 'bg-white/10 text-white/70 hover:bg-white/20 hover:text-white'
                        }`}
                      >
                        {skill}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        );

      case 3:
        return (
          <motion.div
            key="step3"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div className="text-center mb-8">
              <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Star size={32} className="text-white" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">
                Choose Your Interests
              </h2>
              <p className="text-white/70">
                Select the domains that interest you most
              </p>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {interestDomains.map((interest) => (
                <button
                  key={interest}
                  onClick={() => handleInterestToggle(interest)}
                  className={`p-4 rounded-xl text-sm font-medium transition-all duration-300 ${
                    formData.interests.includes(interest)
                      ? 'bg-gradient-to-r from-purple-500 to-pink-600 text-white'
                      : 'bg-white/10 text-white/70 hover:bg-white/20 hover:text-white'
                  }`}
                >
                  {interest}
                </button>
              ))}
            </div>
          </motion.div>
        );

      case 4:
        return (
          <motion.div
            key="step4"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div className="text-center mb-8">
              <div className="w-16 h-16 bg-gradient-to-br from-pink-500 to-orange-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Brain size={32} className="text-white" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">
                Personality Assessment
              </h2>
              <p className="text-white/70">
                Help us understand your personality to find better matches
              </p>
            </div>

            <div className="space-y-8">
              {mbtiQuestions.map((question, index) => (
                <div key={question.id} className="space-y-4">
                  <h3 className="text-lg font-semibold text-white">
                    {index + 1}. {question.question}
                  </h3>
                  <div className="space-y-3">
                    {question.options.map((option) => (
                      <button
                        key={option.value}
                        onClick={() => handleMBTIAnswer(question.id, option.value)}
                        className={`w-full p-4 rounded-xl text-left transition-all duration-300 ${
                          formData.mbtiAnswers[question.id] === option.value
                            ? 'bg-gradient-to-r from-pink-500 to-orange-600 text-white'
                            : 'bg-white/10 text-white/70 hover:bg-white/20 hover:text-white'
                        }`}
                      >
                        {option.text}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen pt-16 pb-20">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Progress Bar */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-2xl font-bold text-white">
              Profile Setup
            </h1>
            <span className="text-white/70">
              Step {currentStep} of {totalSteps}
            </span>
          </div>
          <ProgressBar value={progress} color="blue" />
        </div>

        {/* Main Content */}
        <Card variant="liquid" className="p-8">
          {errors.general && (
            <div className="mb-6 p-4 bg-red-500/20 border border-red-500/30 rounded-lg">
              <p className="text-red-400 text-sm">{errors.general}</p>
            </div>
          )}
          
          <AnimatePresence mode="wait">
            {renderStep()}
          </AnimatePresence>

          {/* Navigation */}
          <div className="flex justify-between items-center mt-12 pt-8 border-t border-white/10">
            <Button
              variant="ghost"
              onClick={prevStep}
              disabled={currentStep === 1}
              icon={<ArrowLeft size={20} />}
            >
              Previous
            </Button>

            <div className="flex space-x-2">
              {[...Array(totalSteps)].map((_, index) => (
                <div
                  key={index}
                  className={`w-2 h-2 rounded-full transition-all duration-300 ${
                    index + 1 <= currentStep
                      ? 'bg-gradient-to-r from-horizon-800 to-horizon-900'
                      : 'bg-white/20'
                  }`}
                />
              ))}
            </div>

            {currentStep < totalSteps ? (
              <Button
                onClick={nextStep}
                disabled={!canProceed()}
                icon={<ArrowRight size={20} />}
              >
                Next
              </Button>
            ) : (
              <Button
                onClick={handleSubmit}
                loading={loading}
                disabled={!canProceed()}
                icon={<CheckCircle size={20} />}
              >
                {loading ? 'Creating Profile...' : 'Complete Setup'}
              </Button>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default ProfileSetupPage;
