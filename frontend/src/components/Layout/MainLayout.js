// src/components/Layout/MainLayout.js
import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import SidebarSwitcher from '../Sidebar/SidebarSwitcher';
import Header from '../Headers/Header';
import routes from '../../routes';
import { getUserRole } from '../../routes';

const MainLayout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [currentUser, setCurrentUser] = useState(null);
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
  // Récupérer le rôle de l'utilisateur
  const userRole = useMemo(() => {
    if (!currentUser) return 'guest';
    return getUserRole(currentUser);
  }, [currentUser]);
  
  // Filtrer les routes en fonction du rôle de l'utilisateur
  const filteredRoutes = useMemo(() => {
    if (!currentUser) return [];
    
    return routes.filter(route => {
      if (!route.allowedRoles && !route.roles) return true;
      const rolesToCheck = route.allowedRoles || route.roles || [];
      const hasAccess = rolesToCheck.includes(userRole);
      
      if (userRole === 'manager' && rolesToCheck.includes('admin')) {
        return true;
      }
      
      return hasAccess;
    });
  }, [currentUser, userRole]);

  // Charger l'utilisateur depuis le stockage local et le contexte d'authentification
  useEffect(() => {
    const loadUser = () => {
      try {
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
          const user = JSON.parse(storedUser);
          setCurrentUser(user);
        } else if (isAuthenticated) {
          // Si l'utilisateur est authentifié mais pas dans le localStorage
          // Rafraîchir la page pour forcer le rechargement des données utilisateur
          window.location.reload();
        } else {
          navigate('/auth/login');
        }
      } catch (error) {
        console.error('Erreur lors de la récupération des informations utilisateur:', error);
        handleLogout();
      }
    };
    
    loadUser();
    
    // Écouter les changements d'authentification
    const handleStorageChange = (e) => {
      if (e.key === 'user' || e.key === 'token') {
        loadUser();
      }
    };
    
    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [navigate, isAuthenticated]);

  useEffect(() => {
    const checkAuthAndRedirect = async () => {
      if (isAuthenticated && currentUser) {
        try {
          let redirectPath = '/';
          
          // Vérifier si c'est un employé ou un administrateur
          if (currentUser.is_superuser || 
              currentUser.role === 'administrateur' || 
              currentUser.role === 'gestionnaire' || 
              currentUser.role === 'employee') {
            redirectPath = '/admin/profile';
          } 
          // Sinon, c'est un client
          else {
            redirectPath = '/client/profile';
          }
          
          if (location.pathname !== redirectPath) {
            console.log('Redirection automatique vers:', redirectPath);
            navigate(redirectPath, { replace: true });
          }
        } catch (err) {
          console.error('Erreur lors de la vérification de l\'authentification:', err);
        }
      }
    };

    checkAuthAndRedirect();
  }, [isAuthenticated, currentUser, location.pathname, navigate]);

  const handleLogout = () => {
    logout();
    navigate('/auth/login');
  };

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  // Si l'utilisateur n'est pas authentifié, on ne rend rien
  if (!currentUser) {
    return null;
  }

  
  return (
    <div className="wrapper">
      {/* Barre latérale */}
      <SidebarSwitcher 
        forceSidebar={shouldForceClientSidebar ? 'client' : null} 
      />
      
      <div className="main-panel">
        {/* En-tête */}
        <Header 
          toggleSidebar={toggleSidebar}
          sidebarOpen={sidebarOpen}
          onLogout={handleLogout}
          user={currentUser}
        />
        
        {/* Contenu principal */}
        <div className="content">
          <div>
            {children}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MainLayout;