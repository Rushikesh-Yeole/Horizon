import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  ArrowRight, 
  Brain, 
  Target, 
  Zap, 
  Users, 
  TrendingUp, 
  Star,
  Play
} from 'lucide-react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';

const HomePage: React.FC = () => {
  const features = [
    {
      icon: Brain,
      title: 'AI-Powered Matching',
      description: 'Advanced algorithms analyze your skills, personality, and preferences to find perfect career matches.',
    },
    {
      icon: Target,
      title: 'Personalized Career Paths',
      description: 'Discover tailored career progression routes with clear milestones and growth opportunities.',
    },
    {
      icon: Zap,
      title: 'Real-time Job Listings',
      description: 'Access curated job opportunities with intelligent ranking based on your profile and preferences.',
    },
    {
      icon: Users,
      title: 'Community Insights',
      description: 'Learn from others in your field and get insights from successful professionals.',
    },
  ];


  return (
    <div className="pt-16">
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        {/* Background Elements */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-white/5 rounded-full blur-3xl animate-float" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-beige-500/10 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }} />
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-white/3 rounded-full blur-3xl animate-float" style={{ animationDelay: '4s' }} />
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="space-y-8"
          >
            <h1 className="text-5xl md:text-7xl font-bold leading-tight">
              <span className="gradient-text">Discover Your</span>
              <br />
              <span className="text-white">Perfect Career</span>
            </h1>
            
            <p className="text-xl md:text-2xl text-white/70 max-w-3xl mx-auto leading-relaxed">
              AI-powered career intelligence that analyzes your skills, personality, and aspirations to guide you toward your ideal professional path.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Link to="/register">
                <Button size="lg" icon={<Play size={20} />}>
                  Get Started Free
                </Button>
              </Link>
              <Link to="/jobs">
                <Button variant="glass" size="lg">
                  Explore Jobs
                </Button>
              </Link>
            </div>

          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Why Choose <span className="gradient-text">Horizon</span>?
            </h2>
            <p className="text-xl text-white/70 max-w-3xl mx-auto">
              Our platform combines cutting-edge AI with intuitive design to revolutionize how you approach career development.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  viewport={{ once: true }}
                >
                  <Card variant="liquid" className="p-6 h-full">
                    <div className="text-center space-y-4">
                      <div className="w-16 h-16 bg-gradient-to-br from-horizon-800 to-horizon-900 border border-white/20 rounded-2xl flex items-center justify-center mx-auto">
                        <Icon size={32} className="text-white" />
                      </div>
                      <h3 className="text-xl font-semibold text-white">
                        {feature.title}
                      </h3>
                      <p className="text-white/70 text-sm leading-relaxed">
                        {feature.description}
                      </p>
                    </div>
                  </Card>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20 bg-horizon-900/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              How It <span className="gradient-text">Works</span>
            </h2>
            <p className="text-xl text-white/70 max-w-3xl mx-auto">
              Get started in minutes and discover your perfect career path with our intelligent platform.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                step: '01',
                title: 'Create Your Profile',
                description: 'Upload your resume, complete our MBTI-style questionnaire, and tell us about your skills and interests.',
                icon: <Users size={24} />,
              },
              {
                step: '02',
                title: 'AI Analysis',
                description: 'Our advanced algorithms analyze your profile against our knowledge base of skills, domains, and personality traits.',
                icon: <Brain size={24} />,
              },
              {
                step: '03',
                title: 'Discover & Grow',
                description: 'Explore personalized job matches and actionable career paths plans tailored just for you.',
                icon: <TrendingUp size={24} />,
              },
            ].map((step, index) => (
              <motion.div
                key={step.step}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.2 }}
                viewport={{ once: true }}
                className="relative"
              >
                <Card variant="glass" className="p-8 h-full">
                  <div className="space-y-6">
                    <div className="flex items-center space-x-4">
                      <div className="w-12 h-12 bg-gradient-to-br from-horizon-800 to-horizon-900 border border-white/20 rounded-xl flex items-center justify-center text-white font-bold text-lg">
                        {step.step}
                      </div>
                      <div className="w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center text-white">
                        {step.icon}
                      </div>
                    </div>
                    <h3 className="text-2xl font-semibold text-white">
                      {step.title}
                    </h3>
                    <p className="text-white/70 leading-relaxed">
                      {step.description}
                    </p>
                  </div>
                </Card>

                {index < 2 && (
                  <div className="hidden md:block absolute top-1/2 -right-4 transform -translate-y-1/2">
                    <ArrowRight size={24} className="text-white/30" />
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </section>


      {/* CTA Section */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="space-y-8"
          >
            <h2 className="text-4xl md:text-5xl font-bold text-white">
              Ready to Transform Your <span className="gradient-text">Career</span>?
            </h2>
            <p className="text-xl text-white/70 max-w-2xl mx-auto">
              Discover your perfect career path with Horizon's AI-powered platform.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Link to="/register">
                <Button size="lg" icon={<ArrowRight size={20} />}>
                  Start Your Journey
                </Button>
              </Link>
              <Link to="/career-tree">
                <Button variant="glass" size="lg">
                  Explore Career Tree
                </Button>
              </Link>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
