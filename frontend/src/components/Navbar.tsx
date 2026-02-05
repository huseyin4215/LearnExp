import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

const Navbar: React.FC = () => {
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    setIsProfileOpen(false);
    // TODO: Logout işlemleri (token silme vs.)
    navigate('/login');
  };

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-40">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <Link to="/" className="flex-shrink-0">
              <h1 className="text-2xl font-bold text-indigo-600">XXX</h1>
              <p className="text-xs text-gray-500">Smart Academic Discovery</p>
            </Link>
          </div>
          <div className="hidden md:block">
            <div className="ml-10 flex items-baseline space-x-4">
              <Link to="/" className={`${isActive('/') ? 'text-indigo-600' : 'text-gray-600'} hover:text-indigo-600 px-3 py-2 rounded-md text-sm font-medium`}>Dashboard</Link>
              <Link to="/search" className={`${isActive('/search') ? 'text-indigo-600' : 'text-gray-600'} hover:text-indigo-600 px-3 py-2 rounded-md text-sm font-medium`}>Search</Link>
              <Link to="/library" className={`${isActive('/library') ? 'text-indigo-600' : 'text-gray-600'} hover:text-indigo-600 px-3 py-2 rounded-md text-sm font-medium`}>My Library</Link>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="relative">
              <div
                className="w-8 h-8 bg-indigo-600 rounded-full flex items-center justify-center cursor-pointer hover:bg-indigo-700"
                onClick={() => setIsProfileOpen(!isProfileOpen)}
              >
                <span className="text-white text-sm font-medium">AK</span>
              </div>
              {isProfileOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50 border border-gray-200">
                  <Link to="/profile" onClick={() => setIsProfileOpen(false)} className="w-full text-left block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">View Profile</Link>
                  <Link to="/settings" onClick={() => setIsProfileOpen(false)} className="w-full text-left block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Settings</Link>
                  <div className="border-t border-gray-100"></div>
                  <button onClick={handleLogout} className="w-full text-left block px-4 py-2 text-sm text-red-600 hover:bg-red-50">Log Out</button>
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>
    </header>
  );
};

export default Navbar;
