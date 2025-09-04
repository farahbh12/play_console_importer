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
  // Référence pour stocker le contexte d'authentification
  const [authContext, setAuthContext] = useState(null);
  
  // Fonction pour enregistrer le contexte d'authentification
  const handleAuthContext = (context) => {
    if (context && !window.authContext) {
      window.authContext = context;
      setAuthContext(context);
    }
    return context;
  };
  
  return (
    <AuthProvider>
      {({ ...authProps }) => {
        // Enregistrer le contexte d'authentification
        const context = handleAuthContext(authProps);
        
        return (
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
                <ProtectedRoute allowedRoles={['owner', 'membre_invite', 'client']}>
                  <ClientLayout />
                </ProtectedRoute>
              } />
              
              <Route path="/" element={<Navigate to="/client/profile" replace />} />
              <Route path="*" element={<Navigate to="/client/profile" replace />} />
            </Routes>
          </BrowserRouter>
        );
      }}
    </AuthProvider>
  );
}

export default App;