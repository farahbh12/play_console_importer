import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Route, Routes, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';

// Styles
import 'react-toastify/dist/ReactToastify.css';
import "./assets/plugins/nucleo/css/nucleo.css";
import "@fortawesome/fontawesome-free/css/all.min.css";
import './assets/scss/argon-dashboard-react.scss';

// Layouts
import AdminLayout from "./layouts/Admin";
import AuthLayout from "./layouts/Auth";
import ClientLayout from "./layouts/Client";

// Pages d'authentification
import ForgotPassword from "./views/examples/ForgotPassword";
import ResetPassword from "./views/examples/ResetPassword";
import Login from "./views/examples/Login";
import Register from "./views/examples/Register";
import PasswordResetRedirect from './views/examples/PasswordResetRedirect';

// Composant pour gérer les redirections
const PrivateRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '100vh' }}>
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Chargement...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated()) {
    return <Navigate to="/auth/login" state={{ from: location }} replace />;
  }

  return children;
};

// Configuration du routeur
const AppRoutes = () => (
  <Routes>
    {/* Routes protégées */}
    <Route path="/admin/*" element={
      <PrivateRoute>
        <AdminLayout />
      </PrivateRoute>
    } />
    
    <Route path="/client/*" element={
      <PrivateRoute>
        <ClientLayout />
      </PrivateRoute>
    } />
    
    {/* Routes publiques */}
    <Route path="/auth/*" element={<AuthLayout />}>
      <Route index element={<Navigate to="login" replace />} />
      <Route path="login" element={<Login />} />
      <Route path="register" element={<Register />} />
      <Route path="forgot-password" element={<ForgotPassword />} />
      <Route path="reset-password/:uid/:token" element={<ResetPassword />} />
    </Route>
    
    {/* Redirections */}
    <Route path="/reset-password-confirm" element={<PasswordResetRedirect />} />
    <Route path="/" element={<Navigate to="/auth/login" replace />} />
    <Route path="*" element={<Navigate to="/auth/login" replace />} />
  </Routes>
);

// Composant principal
const App = () => (
  <BrowserRouter
    future={{
      v7_startTransition: true,
      v7_relativeSplatPath: true
    }}
  >
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  </BrowserRouter>
);

// Rendu de l'application
const root = ReactDOM.createRoot(document.getElementById("root"));

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);