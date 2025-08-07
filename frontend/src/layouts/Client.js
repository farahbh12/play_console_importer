/*!
* Argon Dashboard React - v1.2.4
* Client Layout
*/
import React, { useEffect, useMemo, useState, useContext } from "react";
import { useLocation, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { Container, Spinner } from "reactstrap";

// Components
import ClientNavbar from "../components/Navbars/ClientNavbar";
import SidebarSwitcher from "../components/Sidebar/SidebarSwitcher";
import ClientFooter from "../components/Footers/ClientFooter";

// Context
import { useAuth } from "../contexts/AuthContext";

// Routes
import { routes } from "../routes";
import auth from "../services/auth";

const Client = (props) => {
  const { user, loading: authLoading } = useAuth();
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
    console.log('Client layout - État utilisateur:', { 
      currentUser, 
      isClient: currentUser?.user_type === 'client',
      currentPath: location.pathname 
    });
  }, [currentUser, location.pathname]);

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
        
        console.log('Enregistrement de la route client:', { 
          original: prop.path, 
          cleanPath,
          component: prop.component?.name || 'Anonymous',
          exact: prop.exact
        });
        
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
    console.log('ClientLayout: Aucun utilisateur connecté, redirection vers /auth/login');
    return <Navigate to="/auth/login" state={{ from: location }} replace />;
  }

  // Vérifier si l'utilisateur est un client
  const isClient = currentUser?.role === 'client';
  
  // Déterminer si l'utilisateur peut accéder à l'interface client
  // Les Owner peuvent accéder à toutes les interfaces
  const canAccessClientInterface = isClient || 
    currentUser?.role === 'Owner' || 
    currentUser?.role === 'owner' || 
    currentUser?.is_superuser;
  
  // Si l'utilisateur est connecté mais ne peut pas accéder à l'interface client, rediriger vers l'interface admin
  if (currentUser && !canAccessClientInterface) {
    console.log(`ClientLayout: L'utilisateur est un ${currentUser.role}, redirection vers /admin/index`);
    return <Navigate to="/admin/index" replace />;
  }

  return (
    <div className="g-sidenav-show g-sidenav-pinned">
      <SidebarSwitcher />
      <div className="main-content" id="panel">
        <ClientNavbar user={currentUser} onLogout={() => {
          console.log('Déconnexion depuis ClientLayout');
          auth.logout();
          navigate('/auth/login');
        }} />
        <div className="container-fluid mt-4">
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