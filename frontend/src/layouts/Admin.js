/*!

=========================================================
* Argon Dashboard React - v1.2.4
=========================================================

* Product Page: https://www.creative-tim.com/product/argon-dashboard-react
* Copyright 2024 Creative Tim (https://www.creative-tim.com)
* Licensed under MIT (https://github.com/creativetimofficial/argon-dashboard-react/blob/master/LICENSE.md)

* Coded by Creative Tim

=========================================================

* The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

*/
import React, { useEffect, useRef } from "react";
import { useLocation, Route, Routes, Navigate, Link } from "react-router-dom";
import { Container } from "reactstrap";
import AdminNavbar from "../components/Navbars/AdminNavbar";
import AdminFooter from "../components/Footers/AdminFooter";
import SidebarSwitcher from "../components/Sidebar/SidebarSwitcher";
import { useAuth } from "../contexts/AuthContext";
import { routes } from "../routes";
import RoleProtectedRoute from "../components/RoleProtectedRoute";

const Admin = (props) => {
  const mainContent = useRef(null);
  const location = useLocation();
  const { currentUser, loading } = useAuth();

  // Récupérer les routes filtrées
  // Définir la fonction getUserRole avant de l'utiliser dans useMemo
  const getUserRole = () => {
    if (!currentUser) return 'guest';

    // Vérifier d'abord le type d'utilisateur (user_type) s'il est défini
    if (currentUser.user_type) {
      const userType = currentUser.user_type.toLowerCase();
      if (userType === 'employee') return 'manager';
      if (userType === 'client') return 'client';
      if (userType === 'admin') return 'admin';
      if (userType === 'manager') return 'manager';
    }
    
    // Vérifier le rôle (role) s'il est défini
    if (currentUser.role) {
      const userRole = currentUser.role.toLowerCase();
      
      if (currentUser.is_superuser || userRole === 'admin' || userRole === 'administrateur') {
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
    if (currentUser.employee_id) {
      return 'manager';
    }
    
    // Par défaut, considérer comme client
    return 'client';
  };

  const filteredRoutes = React.useMemo(() => {
    if (!currentUser) return [];
    
    const userRole = getUserRole();
    
    return routes.filter(route => {
      // Vérifier si la route a un layout
      if (!route.layout) return false;
      
      // Vérifier si la route est dans le bon layout
      if (route.layout !== '/admin') return false;
      
      // Si la route n'a pas de restriction de rôle, l'autoriser
      if (!route.allowedRoles || route.allowedRoles.length === 0) return true;
      
      // Vérifier si l'utilisateur a un des rôles requis
      return route.allowedRoles.some(role => {
        // Les administrateurs ont accès à tout
        if (userRole === 'admin') return true;
        // Les managers ont accès aux routes admin
        if (userRole === 'manager' && role === 'admin') return true;
        // Vérifier si le rôle correspond
        return role.toLowerCase() === userRole.toLowerCase();
      });
    });
  }, [currentUser]);

  useEffect(() => {
    document.documentElement.scrollTop = 0;
    document.scrollingElement.scrollTop = 0;
    if (mainContent.current) {
      mainContent.current.scrollTop = 0;
    }
  }, [location]);

  // Filtrer les routes en fonction du rôle de l'utilisateur
  const getFilteredRoutes = () => {
    if (!currentUser) return [];
    
    // Utiliser la même logique de détection que getUserRole
    let userRole = 'guest';
    if (currentUser.is_superuser || currentUser.role === 'administrateur' || currentUser.role === 'admin') {
      userRole = 'admin';
    } else if (currentUser.role === 'gestionnaire' || 
               currentUser.role === 'manager' || 
               currentUser.role === 'employee' ||
               currentUser.user_type === 'employee' ||
               currentUser.employee_id) {
      userRole = 'manager';
    } else if (currentUser.role === 'client' || 
               currentUser.role === 'Owner' || 
               currentUser.role === 'owner' ||
               currentUser.user_type === 'client') {
      userRole = 'client';
    }
    

    
    return routes.filter(route => {
      // Inclure les routes sans allowedRoles
      if (!route.allowedRoles) return true;
      
      // Vérifier si l'utilisateur a accès à cette route
      const hasAccess = route.allowedRoles.includes(userRole);
      
      // Les gestionnaires ont accès aux routes admin (accès partagé)
      if (userRole === 'manager' && route.allowedRoles.includes('admin')) {
        return true;
      }
      
      // Les admins ont accès à toutes les routes admin et manager
      if (userRole === 'admin' && (route.allowedRoles.includes('admin') || route.allowedRoles.includes('manager'))) {
        return true;
      }
      
      return hasAccess;
    });
  };

  // La fonction getBrandText est définie plus bas avec une implémentation améliorée

  // Afficher un indicateur de chargement pendant la vérification de l'authentification
  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ height: '100vh' }}>
        <div className="text-center">
          <div className="spinner-border text-primary" role="status">
            <span className="sr-only">Chargement...</span>
          </div>
          <p className="mt-2">Chargement de votre espace...</p>
        </div>
      </div>
    );
  }

  // Rediriger vers la page de connexion si l'utilisateur n'est pas connecté
  if (!currentUser) {
    return <Navigate to="/auth/login" state={{ from: location }} replace />;
  }

  // Utiliser la fonction getUserRole définie au début du composant
  const userRole = getUserRole();
  
  // Fonction pour obtenir le texte de la marque en fonction de l'URL
  const getBrandText = (pathname) => {
    const route = routes.find(route => route.path === pathname);
    return route ? route.name : 'Tableau de bord';
  };

  
  // Rediriger les clients (y compris Owner) vers leur tableau de bord
  if (userRole === 'client') {

    return <Navigate to="/client/dashboard" replace />;
  }
  
  // Les admin et manager ont accès à l'interface admin


  // Rendu de la barre de navigation appropriée en fonction du rôle
  const renderNavbar = () => {
    const navbarProps = {
      ...props,
      brandText: getBrandText(location.pathname),
      user: currentUser
    };
    
    return <AdminNavbar {...navbarProps} />;
  };

  // La variable filteredRoutes est déjà définie au début du composant avec useMemo

  return (
    <div className="g-sidenav-show g-sidenav-pinned">
      <SidebarSwitcher />
      <div className="main-content" ref={mainContent}>
        {renderNavbar()}
        <Container fluid className="mt-4">
          <Routes>
            {filteredRoutes.map((route, key) => {
              // Gérer les redirections
              if (route.redirect) {
                return (
                  <Route 
                    key={`redirect-${key}`} 
                    path={route.path.replace(/^\/admin/, '')} 
                    element={<Navigate to={route.redirect} replace />} 
                  />
                );
              }
              
              // Vérifier si la route est dans le bon layout
              if (route.layout === "/admin") {
                const RouteComponent = route.component;
                
                if (!RouteComponent) {
                  console.error(`Composant non trouvé pour la route: ${route.path}`);
                  return null;
                }
                
                // Créer un chemin relatif pour la route
                const routePath = route.path.startsWith('/admin') 
                  ? route.path.substring(6) // Enlever '/admin' du début
                  : route.path;
                
                // Nettoyer le chemin pour éviter les doubles slashes
                const cleanPath = routePath.replace(/^\/+/, '');
                
                console.log(`Rendu de la route: ${cleanPath} (${route.name})`);
                
                return (
                  <Route
                    key={`route-${key}`}
                    path={cleanPath}
                    element={
                      route.allowedRoles ? (
                        <RoleProtectedRoute allowedRoles={route.allowedRoles}>
                          <RouteComponent />
                        </RoleProtectedRoute>
                      ) : (
                        <RouteComponent />
                      )
                    }
                  />
                );
              }
              
              return null;
            })}
            
            {/* Route par défaut pour les chemins non trouvés */}
            <Route 
              key="not-found" 
              path="*" 
              element={
                <div className="text-center py-5">
                  <h1 className="display-1 text-danger">404</h1>
                  <p className="lead">Page non trouvée</p>
                  <p>La page que vous recherchez n'existe pas ou vous n'avez pas les droits d'accès.</p>
                  <Link to="/admin" className="btn btn-primary">
                    Retour à l'accueil
                  </Link>
                </div>
              } 
            />
          </Routes>
        </Container>
        <div>
          <AdminFooter />
        </div>
      </div>
    </div>
  );
};

export default Admin;