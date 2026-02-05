import React from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import Navbar from './components/Navbar';
import ChatOverlay from './components/ChatOverlay';
import Dashboard from './views/Dashboard';
import SearchDashboard from './views/SearchDashboard';
import MyLibrary from './views/MyLibrary';
import Profile from './views/Profile';
import Settings from './views/Settings';
import Login from './pages/Login';
import Register from './pages/Register';

const App: React.FC = () => {
  const location = useLocation();
  const isAuthPage = location.pathname === '/login' || location.pathname === '/register';

  // Auth sayfalarında farklı layout kullan
  if (isAuthPage) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
      </Routes>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Navbar />

      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/search" element={<SearchDashboard />} />
          <Route path="/library" element={<MyLibrary />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>

      <ChatOverlay />
    </div>
  );
};

export default App;
