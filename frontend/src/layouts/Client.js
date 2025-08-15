/*!
* Argon Dashboard React - v1.2.4
* Client Layout
*/
import React, { useState, useEffect, useMemo } from 'react';
import { useLocation, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import {   Spinner } from "reactstrap";

// Components
import ClientNavbar from "../components/Navbars/ClientNavbar";
import SidebarSwitcher from "../components/Sidebar/SidebarSwitcher";
import ClientFooter from "../components/Footers/ClientFooter";




// Routes
import { routes } from "../routes";
import auth from "../services/auth";

const Client = (props) => {
 
  const location = useLocation();
  const navigate = useNavigate();
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Effet pour charger l'utilisateur au démarrage
  useEffect(() => {
    const loadUser = async () => {
      try {
        const user = await auth.getCurrentUser();
        setCurrentUser(user);
      } catch (error) {
        console.error('Erreur lors du chargement de l\'utilisateur:', error);
      } finally {
        setLoading(false);
      }
    };

    loadUser();
  }, []);

  // Effet pour le défilement en haut de page lors du changement de route
  useEffect(() => {
    document.documentElement.scrollTop = 0;
    document.scrollingElement.scrollTop = 0;
  }, [location]);

  // Logs de débogage
  useEffect(() => {
    console.group('Client layout - État utilisateur');
    console.log({
      currentUser: currentUser, 
      isClient: currentUser?.user_type === 'client',
      currentPath: location.pathname 
    });
    console.groupEnd();
  }, [currentUser, location.pathname]);

  // Forcer les membres invités à rester sur /client/source ou /client/destination
  useEffect(() => {
    // Toujours déclarer le hook, conditionner la logique à l'intérieur
    if (!currentUser) return;
    const role = currentUser?.role;
    if (role === 'MEMBRE_INVITE') {
      const allowed = ['/client/source', '/client/destination', '/client/profile'];
      if (!allowed.includes(location.pathname)) {
        navigate('/client/source', { replace: true });
      }
    }
  }, [currentUser, location.pathname, navigate]);

  // Mémoriser les routes pour éviter des recalculs inutiles
  const clientRoutes = useMemo(() => {
    return routes
      .filter(route => route.layout === "/client")
      .map((prop, key) => {
        if (prop.redirect) {
          return (
            <Route 
              path={prop.path.replace(/^\/client/, '')} 
              element={<Navigate to={prop.redirect} replace />} 
              key={key} 
            />
          );
        }
        
        // Nettoyer le chemin en enlevant le préfixe /client s'il existe
        const cleanPath = prop.path.replace(/^\/client\/?/, '');

        
        const RouteComponent = prop.component;
        return (
          <Route
            path={cleanPath}
            element={React.createElement(RouteComponent, { ...props, key: key })}
            key={key}
          />
        );
      });
  }, [props]);

  // Afficher un indicateur de chargement pendant la vérification de l'authentification
  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ height: '100vh' }}>
        <div className="text-center">
          <Spinner color="primary" />
          <p className="mt-2">Chargement de votre espace client...</p>
        </div>
      </div>
    );
  }

  // Vérifier l'authentification et le type d'utilisateur
  if (!currentUser) {

    return <Navigate to="/auth/login" state={{ from: location }} replace />;
  }

  // Normaliser le rôle utilisateur
  const role = currentUser?.role;
  const userType = currentUser?.user_type;
  const isClient = role === 'client' || role === 'Owner' || role === 'owner' || role === 'MEMBRE_INVITE' || userType === 'client';

  // Autoriser l'interface client pour Owner et Membre Invité (et clients en général)
  const canAccessClientInterface = isClient || currentUser?.is_superuser;

  // Si l'utilisateur ne peut pas accéder à l'interface client, rediriger vers l'interface admin
  if (currentUser && !canAccessClientInterface) {
    return <Navigate to="/admin/index" replace />;
  }


  return (
    <div className="g-sidenav-show g-sidenav-pinned">
      <SidebarSwitcher />
      <div className="main-content" id="panel">
        <ClientNavbar user={currentUser} onLogout={() => {

          auth.logout();
          navigate('/auth/login');
        }} />
        <div>
          <Routes>
            {clientRoutes}
          </Routes>
        </div>
        <ClientFooter />
      </div>
    </div>
  );
};

export default Client;