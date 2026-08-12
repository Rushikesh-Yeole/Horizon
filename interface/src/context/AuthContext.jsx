import { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';
const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(() => localStorage.getItem('horizon_token'));
  const [email, setEmail] = useState(() => localStorage.getItem('horizon_email'));
  
  // Derived state! Always synchronous with token.
  const isAuthenticated = !!token;  
  const [loading, setLoading] = useState(false);

  // Configure global API headers so you don't have to repeat it
  useEffect(() => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      localStorage.setItem('horizon_token', token);
      if (email) localStorage.setItem('horizon_email', email);
    } else {
      delete api.defaults.headers.common['Authorization'];
      localStorage.removeItem('horizon_token');
      localStorage.removeItem('horizon_email');
    }
  }, [token, email]);

  const login = (jwt, userEmail) => {
    setToken(jwt);
    if (userEmail) {
      setEmail(userEmail);
      if (userEmail === 'demo@horizon.com') {
        localStorage.setItem('demo_session_id', crypto.randomUUID());
        localStorage.setItem('demo_credits', '100');
        localStorage.setItem('show_demo_welcome', 'true');
      }
    }
  };
  
  const logout = () => {
    setToken(null);
    setEmail(null);
    localStorage.removeItem('demo_session_id');
    localStorage.removeItem('demo_credits');
  };

  return (
    <AuthContext.Provider value={{ token, email, isAuthenticated, login, logout, loading, setLoading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);