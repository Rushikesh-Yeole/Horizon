import React from 'react';
import { Link } from 'react-router-dom';
import { Github, Linkedin, Twitter, Mail } from 'lucide-react';

const Footer: React.FC = () => {
  return (
    <footer className="bg-horizon-900/50 backdrop-blur-xl border-t border-white/10 mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">H</span>
              </div>
              <span className="text-xl font-bold gradient-text">Horizon</span>
            </div>
            <p className="text-white/60 text-sm leading-relaxed">
              AI-powered personalized career and skills advisor platform that helps you discover your perfect career path.
            </p>
            <div className="flex space-x-4">
              <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="text-white/60 hover:text-white transition-colors duration-300">
                <Github size={20} />
              </a>
              <a href="https://linkedin.com" target="_blank" rel="noopener noreferrer" className="text-white/60 hover:text-white transition-colors duration-300">
                <Linkedin size={20} />
              </a>
              <a href="https://twitter.com" target="_blank" rel="noopener noreferrer" className="text-white/60 hover:text-white transition-colors duration-300">
                <Twitter size={20} />
              </a>
              <a href="mailto:contact@horizon.com" className="text-white/60 hover:text-white transition-colors duration-300">
                <Mail size={20} />
              </a>
            </div>
          </div>

          {/* Product */}
          <div className="space-y-4">
            <h3 className="text-white font-semibold">Product</h3>
            <ul className="space-y-2">
              <li>
                <Link to="/jobs" className="text-white/60 hover:text-white transition-colors duration-300 text-sm">
                  Job Listings
                </Link>
              </li>
              <li>
                <Link to="/career-tree" className="text-white/60 hover:text-white transition-colors duration-300 text-sm">
                  Career Tree
                </Link>
              </li>
              <li>
                <Link to="/profile-setup" className="text-white/60 hover:text-white transition-colors duration-300 text-sm">
                  Profile Setup
                </Link>
              </li>
            </ul>
          </div>

          {/* Company */}
          <div className="space-y-4">
            <h3 className="text-white font-semibold">Company</h3>
            <ul className="space-y-2">
              <li>
                <a href="/about" className="text-white/60 hover:text-white transition-colors duration-300 text-sm">
                  About Us
                </a>
              </li>
              <li>
                <a href="/careers" className="text-white/60 hover:text-white transition-colors duration-300 text-sm">
                  Careers
                </a>
              </li>
              <li>
                <a href="/contact" className="text-white/60 hover:text-white transition-colors duration-300 text-sm">
                  Contact
                </a>
              </li>
            </ul>
          </div>

          {/* Support */}
          <div className="space-y-4">
            <h3 className="text-white font-semibold">Support</h3>
            <ul className="space-y-2">
              <li>
                <a href="/help" className="text-white/60 hover:text-white transition-colors duration-300 text-sm">
                  Help Center
                </a>
              </li>
              <li>
                <a href="/privacy" className="text-white/60 hover:text-white transition-colors duration-300 text-sm">
                  Privacy Policy
                </a>
              </li>
              <li>
                <a href="/terms" className="text-white/60 hover:text-white transition-colors duration-300 text-sm">
                  Terms of Service
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-white/10 mt-8 pt-8 flex flex-col sm:flex-row justify-between items-center">
          <p className="text-white/60 text-sm">
            © 2024 Horizon. All rights reserved.
          </p>
          <p className="text-white/60 text-sm mt-2 sm:mt-0">
            Built with ❤️ for the future of careers
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
