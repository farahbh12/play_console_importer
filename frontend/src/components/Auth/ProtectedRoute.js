// src/components/Auth/ProtectedRoute.js
import React, { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

/**
 * Composant de protection de route qui vérifie l'authentification et les rôles
 * @param {Object} props - Les propriétés du composant
 * @param {React.ReactNode} props.children - Le contenu à afficher si l'accès est autorisé
 * @param {string|string[]} [props.allowedRoles=[]] - Les rôles ou rôles autorisés à accéder à la route
 * @param {boolean} [props.requireVerification=false] - Si l'utilisateur doit être vérifié
 * @returns {JSX.Element} Le composant de protection de route
 */
const ProtectedRoute = ({ 
  children, 
  allowedRoles = [], 
  requireVerification = false 
}) => {
  const { 
    currentUser, 
    loading, 
    isAuthenticated, 
    hasRole 
  } = useAuth();
  
  const location = useLocation();
  const currentPath = location.pathname;
  
  // Normaliser les rôles autorisés en tableau
  const normalizedRoles = Array.isArray(allowedRoles) 
    ? allowedRoles 
    : [allowedRoles].filter(Boolean);
  
  // Logs de débogage
  useEffect(() => {
    console.group('ProtectedRoute - État de l\'authentification');
    console.log('Chemin actuel:', currentPath);
    console.log('Utilisateur:', currentUser);
    console.log('Chargement:', loading);
    console.log('Authentifié:', isAuthenticated());
    console.log('Rôles autorisés:', normalizedRoles);
    console.log('Vérification email requise:', requireVerification);
    console.groupEnd();
  }, [currentPath, currentUser, loading, normalizedRoles, requireVerification]);

  // Afficher un indicateur de chargement pendant la vérification
  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '60vh' }}>
        <div className="text-center">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Chargement...</span>
          </div>
          <p className="mt-2 text-muted">Vérification des autorisations en cours...</p>
        </div>
      </div>
    );
  }

  // Vérifier si l'utilisateur est authentifié
  const userIsAuthenticated = isAuthenticated();
  
  // Récupérer les informations utilisateur depuis le localStorage
  const user = currentUser || JSON.parse(localStorage.getItem('user') || '{}');
  
  // Vérifier si c'est la première connexion (pas d'abonnement)
  const isFirstLogin = user?.isFirstLogin === true;
  
  // Rediriger vers la page de connexion si non authentifié
  if (!userIsAuthenticated) {
    console.log('ProtectedRoute: Utilisateur non authentifié, redirection vers /auth/login');
    return (
      <Navigate 
        to="/auth/login" 
        state={{ 
          from: { 
            pathname: currentPath,
            search: location.search,
            hash: location.hash
          } 
        }} 
        replace 
      />
    );
  }
  
  // Rediriger vers la page d'abonnement si c'est la première connexion
  // et que l'utilisateur n'est pas déjà sur la page d'abonnement
  if (isFirstLogin && !currentPath.includes('/client/subscription')) {
    console.log('ProtectedRoute: Première connexion, redirection vers /client/subscription?firstLogin=true');
    return (
      <Navigate 
        to="/client/subscription?firstLogin=true" 
        replace 
      />
    );
  }

  // Vérifier si l'utilisateur est vérifié si nécessaire
  if (requireVerification && !currentUser?.is_verified) {
    console.log('ProtectedRoute: Utilisateur non vérifié, redirection vers /verify-email');
    return (
      <Navigate 
        to="/verify-email" 
        state={{ 
          from: { 
            pathname: currentPath,
            search: location.search,
            hash: location.hash
          } 
        }} 
        replace 
      />
    );
  }
  
  // Vérifier les rôles si spécifiés
  if (normalizedRoles.length > 0) {
    const userHasRequiredRole = normalizedRoles.some(role => hasRole(role));
    
    console.group('ProtectedRoute - Vérification des rôles');
    console.log('Rôles de l\'utilisateur:', {
      isSuperuser: currentUser?.is_superuser,
      userType: currentUser?.user_type,
      role: currentUser?.role
    });
    console.log('Rôles requis:', normalizedRoles);
    console.log('Accès autorisé:', userHasRequiredRole);
    console.groupEnd();
    
    if (!userHasRequiredRole) {
      console.log(`ProtectedRoute: Accès refusé - Rôle(s) requis: ${normalizedRoles.join(', ')}`);
      
      // Déterminer si l'utilisateur est un administrateur ou un employé
      const isAdminOrEmployee = hasRole(['admin', 'employee']);
      const redirectPath = isAdminOrEmployee 
        ? '/admin/unauthorized' 
        : '/client/unauthorized';
      
      return (
        <Navigate 
          to={redirectPath} 
          state={{ 
            from: { 
              pathname: currentPath,
              search: location.search,
              hash: location.hash
            },
            requiredRoles: normalizedRoles
          }} 
          replace 
        />
      );
    }
  }
  
  console.log('ProtectedRoute: Accès autorisé à', currentPath);
  return children;
};

export default ProtectedRoute;