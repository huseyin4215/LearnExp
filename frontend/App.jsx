import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

// Layouts
import DashboardLayout from './layouts/DashboardLayout';

// Views - Lazy loaded for performance
const SearchDashboard = lazy(() => import('./views/SearchDashboard'));
const MyLibrary = lazy(() => import('./views/MyLibrary'));
const Settings = lazy(() => import('./views/Settings'));

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<div style={{ padding: '20px' }}>Loading...</div>}>
        <Routes>
          <Route path="/" element={<DashboardLayout />}>
            <Route index element={<Navigate to="/search" replace />} />
            <Route path="search" element={<SearchDashboard />} />
            <Route path="library" element={<MyLibrary />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;