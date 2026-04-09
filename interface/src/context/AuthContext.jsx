import { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  // --- DEV BYPASS ---
  // const [token, setToken] = useState(localStorage.getItem('horizon_token'));
  // const [isAuthenticated, setIsAuthenticated] = useState(!!token);
  
  const [token, setToken] = useState('DEV_MOCK_TOKEN');
  const [isAuthenticated, setIsAuthenticated] = useState(true);
  // ------------------
  
  const [loading, setLoading] = useState(false);

  // Configure global Axios headers so you don't have to repeat it
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      // DEV BYPASS: Commented out localstorage to prevent overriding actual tokens later
      // localStorage.setItem('horizon_token', token);
      // setIsAuthenticated(true);
    } else {
      delete axios.defaults.headers.common['Authorization'];
      // localStorage.removeItem('horizon_token');
      // setIsAuthenticated(false);
    }
  }, [token]);

  const login = (jwt) => setToken(jwt);
  
  const logout = () => {
    // DEV BYPASS: Prevent accidental logouts during dev
    console.log("Logout triggered, but bypassed for dev.");
    // setToken(null);
  };

  return (
    <AuthContext.Provider value={{ token, isAuthenticated, login, logout, loading, setLoading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);