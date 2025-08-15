// src/App.js
import React from 'react';
import './App.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import AdminLayout from './layouts/Admin';
import ClientLayout from './layouts/Client';
import AuthLayout from './layouts/Auth';
import ProtectedRoute from './components/Auth/ProtectedRoute';
import AcceptInvitation from './views/auth/AcceptInvitation';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Route d'acceptation d'invitation - accessible sans authentification */}
          <Route path="/accept-invitation" element={<AcceptInvitation />}>
            <Route path="" element={<AcceptInvitation />} />
            <Route path=":token" element={<AcceptInvitation />} />
          </Route>
          
          {/* Redirection pour les anciens liens */}
          <Route path="/auth/accept-invitation" element={
            <Navigate to="/accept-invitation" replace />
          } />
          
          {/* Autres routes d'authentification */}
          <Route path="/auth/*" element={<AuthLayout />} />
          
          {/* Routes protégées */}
          <Route path="/admin/*" element={
            <ProtectedRoute allowedRoles={['admin', 'manager']}>
              <AdminLayout />
            </ProtectedRoute>
          } />
          
          <Route path="/client/*" element={
            <ProtectedRoute allowedRoles={['owner', 'membre_invite']}>
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