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

      login(res.data.access_token, res.data.email);
      navigate('/');

    } catch (err) {
      setError('Invalid email or password', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4 sm:px-6 pt-20 pb-12">
      <div className="w-full max-w-sm p-8 sm:p-10 rounded-3xl bg-neutral-50/60 border border-neutral-200/80 shadow-2xs">
        
        {/* Title */}
        <div className="text-center mb-8">
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-neutral-950">
            Welcome back
          </h1>
          <p className="text-xs sm:text-sm text-neutral-500 font-mono mt-1.5">Sign in to your Horizon account</p>
        </div>

        {/* Error */}
        {error && (
          <div className="text-xs font-mono font-medium text-rose-600 bg-rose-50 border border-rose-200 p-3 rounded-xl mb-5 text-center">
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleLogin} className="flex flex-col gap-4">
          <div>
            <label className="block text-[10px] font-mono font-bold text-neutral-500 uppercase tracking-wider mb-1.5">Email</label>
            <input
              type="email"
              placeholder="you@example.com"
              className="w-full px-4 py-2.5 bg-white border border-neutral-200 rounded-xl text-xs sm:text-sm text-neutral-950 focus:outline-none focus:border-neutral-950 transition-all font-mono"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="block text-[10px] font-mono font-bold text-neutral-500 uppercase tracking-wider mb-1.5">Password</label>
            <input
              type="password"
              placeholder="••••••••"
              className="w-full px-4 py-2.5 bg-white border border-neutral-200 rounded-xl text-xs sm:text-sm text-neutral-950 focus:outline-none focus:border-neutral-950 transition-all"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="mt-2 bg-neutral-950 text-white py-3 rounded-full text-xs sm:text-sm font-semibold hover:bg-neutral-800 transition-all disabled:opacity-50 shadow-sm"
          >
            {loading ? "Signing in..." : "Sign In &rarr;"}
          </button>
        </form>

        {/* Footer */}
        <p className="text-xs font-mono text-neutral-500 text-center mt-6">
          Don’t have an account?{' '}
          <Link to="/ingest" className="text-neutral-950 font-bold hover:underline">
            Initialize
          </Link>
        </p>

      </div>
    </div>
  );
}