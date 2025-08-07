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
import { useLocation, Route, Routes, Navigate } from "react-router-dom";
import { Container } from "reactstrap";
import AdminNavbar from "../components/Navbars/AdminNavbar";
import AdminFooter from "../components/Footers/AdminFooter";
import SidebarSwitcher from "../components/Sidebar/SidebarSwitcher";
import { useAuth } from "../contexts/AuthContext";
import { routes } from "../routes";

const Admin = (props) => {
  const mainContent = useRef(null);
  const location = useLocation();
  const { currentUser, loading } = useAuth();

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
    
    console.log('Admin Layout - getFilteredRoutes - Rôle utilisateur:', userRole, 'Données:', currentUser);
    
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

  // Obtenir le texte de la marque (titre) en fonction de la route actuelle
  const getBrandText = (path) => {
    const filteredRoutes = getFilteredRoutes();
    const currentRoute = filteredRoutes.find(route => 
      path.includes(route.path) && route.name
    );
    return currentRoute?.name || 'Tableau de bord';
  };

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

  // Vérifier si l'utilisateur a le droit d'accéder à l'administration
  const getUserRole = () => {
    console.log('Admin Layout - Détection du rôle:', {
      is_superuser: currentUser.is_superuser,
      role: currentUser.role,
      user_type: currentUser.user_type,
      employee_id: currentUser.employee_id
    });

    // Administrateurs (accès complet)
    if (currentUser.is_superuser || currentUser.role === 'administrateur' || currentUser.role === 'admin') {
      return 'admin';
    }
    
    // Gestionnaires et employés (accès à l'interface admin)
    if (currentUser.role === 'gestionnaire' || 
        currentUser.role === 'manager' || 
        currentUser.role === 'employee' ||
        currentUser.user_type === 'employee' ||
        currentUser.employee_id) {
      return 'manager';
    }
    
    // Clients
    if (currentUser.role === 'client' || 
        currentUser.role === 'Owner' || 
        currentUser.role === 'owner' ||
        currentUser.user_type === 'client') {
      return 'client';
    }
    
    return 'client'; // Par défaut
  };
  
  const userRole = getUserRole();
  console.log('Admin Layout - Rôle déterminé:', userRole);
  
  // Rediriger les clients (y compris Owner) vers leur tableau de bord
  if (userRole === 'client') {
    console.log('Admin Layout - Redirection vers client dashboard');
    return <Navigate to="/client/dashboard" replace />;
  }
  
  // Les admin et manager ont accès à l'interface admin
  console.log('Admin Layout - Accès autorisé à l\'interface admin');

  return (
    <div className="g-sidenav-show g-sidenav-pinned">
      <SidebarSwitcher />
      <div className="main-content" ref={mainContent}>
        <AdminNavbar
          {...props}
          brandText={getBrandText(location.pathname)}
          user={currentUser}
        />
        <Routes>
          {getFilteredRoutes().map((route, key) => {
            if (route.redirect) {
              return (
                <Route 
                  key={key} 
                  path={route.path} 
                  element={<Navigate to={route.redirect} replace />} 
                />
              );
            }
            
            if (route.layout === "/admin") {
              const RouteComponent = route.component;
              return (
                <Route
                  key={key}
                  path={route.path.replace(/^\/admin/, '')}
                  element={<RouteComponent />}
                />
              );
            }
            
            return null;
          })}
          <Route path="*" element={<Navigate to="/admin/index" replace />} />
        </Routes>
        <Container fluid>
          <AdminFooter />
        </Container>
      </div>
    </div>
  );
};

export default Admin;
