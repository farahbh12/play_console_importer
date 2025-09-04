import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

// Fonction utilitaire pour obtenir le rôle de l'utilisateur
const getUserRole = (user) => {
  if (!user) return 'guest';

  // Vérifier d'abord le type d'utilisateur (user_type) s'il est défini
  if (user.user_type) {
    const userType = user.user_type.toLowerCase();
    if (userType === 'employee') return 'manager';
    if (userType === 'client') return 'client';
    if (userType === 'admin') return 'admin';
    if (userType === 'manager') return 'manager';
  }
  
  // Vérifier le rôle (role) s'il est défini
  if (user.role) {
    const userRole = user.role.toLowerCase();
    
    if (user.is_superuser || userRole === 'admin' || userRole === 'administrateur') {
      return 'admin';
    }
    if (userRole === 'manager' || userRole === 'gestionnaire') {
      return 'manager';
    }
    if (userRole === 'employee' || userRole === 'employé') {
      return 'manager';
    }
    if (userRole === 'client' || userRole === 'owner' || userRole === 'membre_invite') {
      return 'client';
    }
  }
  
  // Vérifier si l'utilisateur a un employee_id (pour la rétrocompatibilité)
  if (user.employee_id) {
    return 'manager';
  }
  
  // Par défaut, considérer comme client
  return 'client';
};

const RoleProtectedRoute = ({ children, allowedRoles = [], ...props }) => {
  const { currentUser } = useAuth();
  const location = useLocation();

  // Journalisation de débogage
  const debugLog = (message, data = '') => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`[RoleProtectedRoute] ${message}`, data);
    }
  };

  // Si l'utilisateur n'est pas connecté, rediriger vers la page de connexion
  if (!currentUser) {
    debugLog('Utilisateur non connecté, redirection vers /auth/login');
    return <Navigate to="/auth/login" state={{ from: location }} replace />;
  }

  // Si le compte est désactivé, rediriger vers la page non autorisée
  if (currentUser.is_active === false) {
    debugLog('Compte désactivé, redirection vers /unauthorized');
    return <Navigate to="/unauthorized" replace />;
  }

  // Obtenir le rôle de l'utilisateur
  const userRole = getUserRole(currentUser);
  debugLog(`Rôle détecté: ${userRole}`, { 
    userType: currentUser.user_type,
    role: currentUser.role,
    isSuperuser: currentUser.is_superuser
  });

  // Journaliser la tentative d'accès
  debugLog(`Tentative d'accès à ${location.pathname}`, {
    allowedRoles,
    currentUser: {
      id: currentUser.id,
      email: currentUser.email,
      role: currentUser.role,
      user_type: currentUser.user_type
    }
  });

  // Vérifier si l'utilisateur a accès à la route
  const hasAccess = allowedRoles.length === 0 || 
                   allowedRoles.some(role => {
                     // Les administrateurs ont accès à tout
                     if (userRole === 'admin') {
                       debugLog('Accès admin accordé');
                       return true;
                     }
                     
                     // Les managers ont accès aux routes admin
                     if (userRole === 'manager' && role === 'admin') {
                       debugLog('Accès manager à une route admin');
                       return true;
                     }
                     
                     // Vérifier si le rôle correspond
                     const accessGranted = role.toLowerCase() === userRole.toLowerCase();
                     if (accessGranted) {
                       debugLog(`Accès accordé pour le rôle: ${userRole}`);
                     }
                     return accessGranted;
                   });

  if (!hasAccess) {
    let redirectTo = '/unauthorized';
    
    // Déterminer la page de redirection en fonction du rôle
    if (userRole === 'employee') {
      redirectTo = '/admin/profile';
    } else if (['admin', 'manager'].includes(userRole)) {
      redirectTo = '/admin/dashboard';
    } else if (['client', 'owner', 'membre_invite'].includes(userRole)) {
      const hasTenant = currentUser?.tenant_id || (currentUser?.tenant && currentUser.tenant.id);
      redirectTo = hasTenant ? '/client/profile' : '/client/subscription?firstLogin=true';
    }
    
    debugLog(`Accès refusé, redirection vers ${redirectTo}`, {
      userRole,
      allowedRoles,
      path: location.pathname,
      redirectTo
    });
    
    return <Navigate to={redirectTo} state={{ from: location }} replace />;
  }

  // Si l'accès est autorisé, cloner les enfants avec les props supplémentaires
  return (children && React.Children.map(children, child => 
    React.cloneElement(child, { ...props, userRole })
  )) || children;
};

export default RoleProtectedRoute;
