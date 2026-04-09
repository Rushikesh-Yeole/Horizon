import { BrowserRouter, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Ingest from './pages/Ingest';
import Discover from './pages/Discover';
import CareerTree from './pages/CareerTree';
import Home from './pages/Home';
import Login from './pages/Login';
import { clsx } from 'clsx';

// 1. Navigation Component (Hidden on Ingest page for minimalism)
const NavBar = () => {
  const { pathname } = useLocation();
  const { isAuthenticated, logout } = useAuth();

  // DEV BYPASS: Commented out so you can always see the nav
  // if (pathname === '/ingest' && !isAuthenticated) return null;

  return (
    <nav className="fixed top-0 w-full z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link to="/" className="font-bold tracking-tight text-xl">Horizon.</Link>
        <div className="flex items-center gap-8">
          {isAuthenticated ? (
            <>
              <Link to="/discover" className="text-sm font-medium text-gray-500 hover:text-black transition-colors">Discover</Link>
              <Link to="/tree" className="text-sm font-medium text-gray-500 hover:text-black transition-colors">Tree</Link>
              <button onClick={logout} className="text-sm font-medium text-red-500 hover:text-red-600 transition-colors">
                Disconnect
              </button>
            </>
          ) : (
             <Link to="/login" className="text-sm font-medium text-black">Login</Link>
          )}
        </div>
      </div>
    </nav>
  );
};

// 2. Protected Route Wrapper
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  
  // DEV BYPASS: Always render children, ignore redirect
  // return isAuthenticated ? children : <Navigate to="/ingest" replace />;
  return children;
};

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="bg-surface min-h-screen text-gray-900 selection:bg-black selection:text-white font-sans">
          <NavBar />
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/ingest" element={<Ingest />} />
            <Route path="/login" element={<Login/>}/>
            <Route path="/discover" element={
              <ProtectedRoute><Discover /></ProtectedRoute>
            } />
            <Route path="/tree" element={
              <ProtectedRoute><CareerTree /></ProtectedRoute>
            } />
          </Routes>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}