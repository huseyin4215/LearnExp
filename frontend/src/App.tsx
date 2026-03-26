import React from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import Navbar from './components/Navbar';
import ChatOverlay from './components/ChatOverlay';
import ProtectedRoute from './components/ProtectedRoute';
import Dashboard from './views/Dashboard';
import SearchDashboard from './views/SearchDashboard';
import MyLibrary from './views/MyLibrary';
import Profile from './views/Profile';
import Settings from './views/Settings';
import News from './views/News';
import Login from './pages/Login';
import Register from './pages/Register';
import CompleteProfile from './pages/CompleteProfile';
import { ThemeProvider } from './contexts/ThemeContext';
import { AuthProvider } from './contexts/AuthContext';

const App: React.FC = () => {
  const location = useLocation();
  const isAuthPage = location.pathname === '/login' || location.pathname === '/register' || location.pathname === '/complete-profile';

  // Auth sayfalarında farklı layout kullan
  if (isAuthPage) {
    return (
      <AuthProvider>
        <ThemeProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/complete-profile" element={<CompleteProfile />} />
          </Routes>
        </ThemeProvider>
      </AuthProvider>
    );
  }

  return (
    <AuthProvider>
      <ThemeProvider>
        <div className="min-h-screen flex flex-col bg-white dark:bg-gray-900 transition-colors">
          <Navbar />

          <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/search" element={<ProtectedRoute><SearchDashboard /></ProtectedRoute>} />
              <Route path="/library" element={<ProtectedRoute><MyLibrary /></ProtectedRoute>} />
              <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
              <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
              <Route path="/news" element={<News />} />
            </Routes>
          </main>

          <ChatOverlay />
        </div>
      </ThemeProvider>
    </AuthProvider>
  );
};

export default App;
