// src/App.js
import React from 'react';
import './App.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import AdminLayout from './layouts/Admin';
import ClientLayout from './layouts/Client';
import AuthLayout from './layouts/Auth';
import ProtectedRoute from './components/Auth/ProtectedRoute';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/auth/*" element={<AuthLayout />} />
          
          <Route path="/admin/*" element={
            <ProtectedRoute allowedRoles={['admin', 'Owner', 'owner']}>
              <AdminLayout />
            </ProtectedRoute>
          } />
          
          <Route path="/client/*" element={
            <ProtectedRoute allowedRoles={['client', 'Owner', 'owner']}>
              <ClientLayout />
            </ProtectedRoute>
          } />
          
          <Route path="/" element={<Navigate to="/client/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/client/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;