import { useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link, Navigate } from 'react-router-dom';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const { login, loading, setLoading, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  if (isAuthenticated) {
    return <Navigate to="/" />;
  }

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await axios.post(`${import.meta.env.VITE_API_URL}/auth/login`, {
        email,
        password
      });

      login(res.data.access_token);
      navigate('/');

    } catch (err) {
      setError('Invalid email or password', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center px-6">
      
      <div className="w-full max-w-sm">
        
        {/* Title */}
        <h1 className="text-2xl font-semibold tracking-tight mb-8 text-center">
          Welcome back
        </h1>

        {/* Error */}
        {error && (
          <p className="text-sm text-red-500 mb-4 text-center">
            {error}
          </p>
        )}

        {/* Form */}
        <form onSubmit={handleLogin} className="flex flex-col gap-4">
          
          <input
            type="email"
            placeholder="Email"
            className="w-full px-4 py-3 bg-white border border-gray-200 rounded-lg 
                       text-sm focus:outline-none focus:border-black transition"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <input
            type="password"
            placeholder="Password"
            className="w-full px-4 py-3 bg-white border border-gray-200 rounded-lg 
                       text-sm focus:outline-none focus:border-black transition"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          <button
            type="submit"
            disabled={loading}
            className="mt-2 bg-black text-white py-3 rounded-lg text-sm font-medium 
                       hover:opacity-90 transition disabled:opacity-50"
          >
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>

        {/* Footer */}
        <p className="text-xs text-gray-500 text-center mt-6">
          Don’t have an account?{' '}
          <Link to="/ingest" className="text-black font-medium hover:underline">
            Initialize
          </Link>
        </p>

      </div>
    </div>
  );
}