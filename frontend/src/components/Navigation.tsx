import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X, BriefcaseBusiness as Briefcase, Waypoints as TreePine, Home } from 'lucide-react';

const Navigation: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  const location = useLocation();

  const navItems = [
    // { name: 'Home', path: '/', icon: Home },
    { name: 'Jobs', path: '/jobs', icon: Briefcase },
    { name: 'Career Tree', path: '/career-tree', icon: TreePine },
  ];

  return (
    <motion.nav
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="fixed top-0 left-16 right-16 z-50 glass-card border-b border-white/10 mt-6 rounded-3xl"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <img 
              src="/horizonLogo.png" 
              alt="Horizon Logo" 
              className="h-8 w-auto"
            />
            <span className="text-xl font-bold text-white">Horizon</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8 ml-36">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              
              return (
                <Link
                  key={item.name}
                  to={item.path}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-all duration-300 ${
                    isActive
                      ? 'bg-white/10 text-white'
                      : 'text-white/70 hover:text-white hover:bg-white/5'
                  }`}
                >
                  <Icon size={18} />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </div>

          {/* Auth Buttons */}
          <div className="hidden md:flex items-center space-x-4">
            <Link
              to="/login"
              className="text-white/70 hover:text-white transition-colors duration-300 text-xl font-bold"
            >
            {(localStorage.getItem('user_id') || "Sign In").replace(/^./, c => c.toUpperCase())}
            </Link>
            <Link
              to="/register"
              className="btn-primary rounded-xl"
            >
              Get Started
            </Link>
          </div>

          {/* Mobile menu button */}
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="md:hidden p-2 rounded-lg text-white/70 hover:text-white hover:bg-white/5 transition-colors duration-300"
          >
            {isOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Navigation */}
        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="md:hidden border-t border-white/10"
            >
              <div className="py-4 space-y-2">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path;
                  
                  return (
                    <Link
                      key={item.name}
                      to={item.path}
                      onClick={() => setIsOpen(false)}
                      className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-300 ${
                        isActive
                          ? 'bg-white/10 text-white'
                          : 'text-white/70 hover:text-white hover:bg-white/5'
                      }`}
                    >
                      <Icon size={20} />
                      <span>{item.name}</span>
                    </Link>
                  );
                })}
                
                <div className="pt-4 border-t border-white/10 space-y-2">
                  <Link
                    to="/login"
                    onClick={() => setIsOpen(false)}
                    className="block px-4 py-3 text-white/70 hover:text-white transition-colors duration-300"
                  >
                  Sign In
                  </Link>
                  <Link
                    to="/register"
                    onClick={() => setIsOpen(false)}
                    className="block mx-4 btn-primary text-center"
                  >
                    Get Started
                  </Link>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.nav>
  );
};

export default Navigation;
