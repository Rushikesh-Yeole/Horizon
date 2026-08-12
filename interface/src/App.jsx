import { BrowserRouter, Routes, Route, Link, useLocation, Navigate, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import api from './services/api';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'sonner';
import { AuthProvider, useAuth } from './context/AuthContext';

const queryClient = new QueryClient();
import Ingest from './pages/Ingest';
import Discover from './pages/Discover';
import CareerTree from './pages/CareerTree';
import Home from './pages/Home';
import Login from './pages/Login';
import Profile from './pages/Profile';
import { clsx } from 'clsx';
import { useQuery } from '@tanstack/react-query';
import NavBar from './components/NavBar';

// 2. Protected Route Wrapper
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  
  return isAuthenticated ? children : <Navigate to="/ingest" replace />;
};

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <div className="bg-surface min-h-screen text-gray-900 selection:bg-black selection:text-white font-sans">
            <Toaster />
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
            <Route path="/profile" element={
              <ProtectedRoute><Profile /></ProtectedRoute>
            } />
          </Routes>
        </div>
      </BrowserRouter>
    </AuthProvider>
    </QueryClientProvider>
  );
}