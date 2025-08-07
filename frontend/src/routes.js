import React from 'react';
import { Navigate } from 'react-router-dom';

// Vues principales
import Index from './views/Index';
import Profile from './views/examples/Profile';

import ClientList from './views/examples/clientList';
import EmployeeList from './views/examples/employeeList';
import AdminProfileEdit from './views/examples/AdminProfileEdit';

// Vues d'authentification
import Login from './views/examples/Login';
import Register from './views/examples/Register';
import ResetPassword from './views/examples/ResetPassword';
import PasswordResetRedirect from './views/examples/PasswordResetRedirect';

// Vues GCS
import DisplayGcsFiles from './views/gcs/DisplayGcsFiles';
import ValidateGcsUri from './views/gcs/ValidateGcsUri';
import DataSourceDetails from './views/gcs/DataSourceDetails';
import GcsConnectorPage from './views/gcs/GcsConnectorPage';


// Vues Abonnements
import AbonnementList from './views/abonnements/AbonnementList';
import SubscriptionPage from './views/abonnements/SubscriptionPage';

// Vues Client
// Le tableau de bord est géré par le composant Index avec des sidebars différents

// Autres composants
import Unauthorized from './views/Unauthorized';
import { useAuth } from './contexts/AuthContext';

// Fonction pour obtenir le rôle de l'utilisateur
export const getUserRole = (user) => {
  if (!user) return 'guest';
  
  // Normaliser le rôle en minuscules pour la comparaison
  const userRole = user.role ? user.role.toLowerCase() : '';
  
  // Vérification pour les administrateurs
  if (user.is_superuser || userRole === 'administrateur' || userRole === 'admin') {
    return 'admin';
  }
  
  // Vérification pour les gestionnaires
  if (userRole === 'gestionnaire' || userRole === 'manager' || user.user_type === 'employee') {
    return 'manager';
  }
  
  // Vérification pour les clients
  if (userRole === 'client' || userRole === 'owner' || user.user_type === 'client') {
    return 'client';
  }
  
  // Par défaut, considérer comme client
  return 'client';
};

// Fonction de vérification des rôles
const withRoleCheck = (Component, allowedRoles = []) => {
  return function ProtectedRoute(props) {
    const { currentUser } = useAuth();

    if (!currentUser) {
      return <Navigate to="/auth/login" replace />;
    }

    const userRole = getUserRole(currentUser);
    
    // Log de débogage
    console.log('withRoleCheck:', {
      userRole,
      allowedRoles,
      currentPath: window.location.pathname
    });
    
    // Vérifier si l'utilisateur peut accéder à la route
    const canAccess = allowedRoles.length === 0 || 
                     allowedRoles.includes(userRole) ||
                     (userRole === 'manager' && allowedRoles.includes('admin'));
    
    // Si l'utilisateur n'a pas accès, rediriger vers la page appropriée
    if (!canAccess) {
      console.log('Accès refusé, redirection...');
      
      // Déterminer la page de redirection en fonction du rôle
      let redirectTo = '/auth/login';
      
      if (userRole === 'admin' || userRole === 'manager' || userRole === 'employee') {
        redirectTo = '/admin/index';
      } else if (userRole === 'client') {
        redirectTo = '/client/dashboard';
      }
      
      return <Navigate to={redirectTo} replace />;
    }

    return <Component {...props} userRole={userRole} />;
  };
};

// Routes protégées (nécessitent une authentification)
const protectedRoutes = [
  // ============================================
  // ROUTE RACINE ADMIN REDIRIGEANT VERS /admin/index
  // ============================================
  {
    path: '/admin',
    exact: true,
    component: () => <Navigate to="/admin/index" replace />,
    layout: '/admin',
    allowedRoles: ['admin', 'manager']
  },
  
  // ============================================
  // ROUTES ADMINISTRATEUR ET GESTIONNAIRE (EMPLOYÉS)
  // ============================================
  {
    path: '/admin/index',
    name: 'Tableau de bord',
    icon: 'ni ni-tv-2 text-primary',
    component: withRoleCheck(Index, ['admin', 'manager']),
    layout: '/admin',
    allowedRoles: ['admin', 'manager'],
    exact: true,
    isIndex: true
  },
  
  // ============================================
  // ROUTES ADMINISTRATEUR ET GESTIONNAIRE
  // ============================================
  {
    path: '/admin/clients',
    name: 'Gestion des clients',
    icon: 'ni ni-single-02 text-blue',
    component: withRoleCheck(ClientList, ['admin', 'manager']),
    layout: '/admin',
    allowedRoles: ['admin', 'manager'],
    section: 'Gestion'
  },
  {
    path: '/admin/subscriptions',
    name: 'Gestion des abonnements',
    icon: 'ni ni-credit-card text-green',
    component: withRoleCheck(AbonnementList, ['admin', 'manager']),
    layout: '/admin',
    allowedRoles: ['admin', 'manager'],
    section: 'Gestion'
  },

  // ============================================
  // ROUTES ADMINISTRATEUR UNIQUEMENT
  // ============================================
  {
    path: '/admin/clients',
    name: 'Gestion des clients',
    icon: 'ni ni-circle-08 text-blue',
    component: withRoleCheck(ClientList, ['admin']),
    layout: '/admin',
    allowedRoles: ['admin'],
    section: 'Administration'
  },
  {
    path: '/admin/employees',
    name: 'Gestion des employés',
    icon: 'ni ni-badge text-yellow',
    component: withRoleCheck(EmployeeList, ['admin']),
    layout: '/admin',
    allowedRoles: ['admin'],
    section: 'Administration'
  },
  {
    path: '/admin/settings',
    name: 'Paramètres',
    icon: 'ni ni-settings-gear-65 text-gray',
    component: withRoleCheck(Index, ['admin']),
    layout: '/admin',
    allowedRoles: ['admin'],
    section: 'Administration'
  },
  
  // ============================================
  // ROUTES PARTAGÉES ADMINISTRATEUR ET GESTIONNAIRE
  // ============================================
  {
    path: '/admin/team-settings',
    name: 'Paramètres d\'équipe',
    icon: 'ni ni-settings-gear-65 text-gray',
    component: withRoleCheck(Index, ['admin', 'manager']),
    layout: '/admin',
    allowedRoles: ['admin', 'manager'],
    section: 'Gestion d\'équipe'
  },
  {
    path: '/admin/profile',
    name: 'Mon Profil',
    icon: 'ni ni-single-02 text-orange',
    component: withRoleCheck(Profile, ['admin', 'manager']),
    layout: '/admin',
    allowedRoles: ['admin', 'manager'],
    section: 'Compte'
  },
  {
    path: '/admin/profile-edit',
    component: withRoleCheck(AdminProfileEdit, ['admin', 'manager']),
    layout: '/admin',
    allowedRoles: ['admin', 'manager']
  },
  {
    path: '/admin/gcs/display-files',
    name: 'Fichiers GCS',
    icon: 'ni ni-folder-17 text-cyan',
    component: withRoleCheck(DisplayGcsFiles, ['admin']),
    layout: '/admin',
    allowedRoles: ['admin']
  },
  
  // ============================================
  // ROUTES PROFIL ADMIN/MANAGER
  // ============================================
  

  // ============================================
  // ROUTES CLIENT
  // ============================================
  {
    path: '/client/dashboard',
    name: 'Tableau de bord',
    icon: 'ni ni-tv-2 text-primary',
    component: withRoleCheck(Index, ['client']),
    layout: '/client',
    allowedRoles: ['client'],
    exact: true
  },
  {
    path: '/client/profile',
    name: 'Mon Profil',
    icon: 'ni ni-single-02 text-orange',
    component: withRoleCheck(Profile, ['client']),
    layout: '/client',
    allowedRoles: ['client']
  },
  
  {
    path: '/client/files',
    name: 'Mes fichiers',
    icon: 'ni ni-folder-17 text-cyan',
    component: withRoleCheck(DisplayGcsFiles, ['client']),
    layout: '/client',
    allowedRoles: ['client']
  },

  {
    path: '/client/validate-gcs-uri',
    name: 'Valider URI GCS',
    icon: 'ni ni-check-bold text-success',
    component: withRoleCheck(ValidateGcsUri, ['client']),
    layout: '/client',
    allowedRoles: ['client']
  },
  {
    path: '/client/data-source',
    name: 'Source de données',
    icon: 'ni ni-cloud-upload-96 text-blue',
    component: withRoleCheck(DataSourceDetails, ['client']),
    layout: '/client',
    allowedRoles: ['client']
  },
  {
    path: '/client/gcs-connector',
    name: 'Connecteur GCS',
    icon: 'ni ni-key-25 text-success',
    component: withRoleCheck(GcsConnectorPage, ['client']),
    layout: '/client',
    allowedRoles: ['client']
  },
  {
    path: '/client/data-source-details/:id',
    component: withRoleCheck(DataSourceDetails, ['client']),
    layout: '/client',
    allowedRoles: ['client']
  },
  {
    path: '/client/subscription',
    name: 'Abonnement',
    icon: 'ni ni-credit-card text-info',
    component: withRoleCheck(SubscriptionPage, ['client']),
    layout: '/client',
    allowedRoles: ['client']
  },


  // ============================================
  // ROUTES PARTAGÉES
  // ============================================
  {
    path: '/profile',
    name: 'Mon Profil',
    icon: 'ni ni-single-02 text-yellow',
    component: withRoleCheck(Profile, ['admin', 'employee', 'client']),
    layout: '/admin',
    allowedRoles: ['admin', 'employee', 'client']
  }
];

// Routes d'authentification (pas besoin d'authentification)
const authRoutes = [
  {
    path: '/login',
    name: 'Connexion',
    component: Login,
    layout: '/auth'
  },
  {
    path: '/register',
    name: 'Inscription',
    component: Register,
    layout: '/auth'
  },
  {
    path: '/reset-password',
    name: 'Réinitialisation du mot de passe',
    component: ResetPassword,
    layout: '/auth'
  },
  {
    path: '/password-reset/:uidb64/:token',
    name: 'Réinitialisation du mot de passe (lien)',
    component: PasswordResetRedirect,
    layout: '/auth'
  },
  {
    path: '/password-reset/confirm',
    name: 'Confirmation de réinitialisation du mot de passe',
    component: PasswordResetRedirect,
    layout: '/auth'
  },
  {
    path: '/unauthorized',
    name: 'Non autorisé',
    component: Unauthorized,
    layout: '/auth'
  }
];

// Combinaison de toutes les routes
export const routes = [
  ...protectedRoutes,
  ...authRoutes,
  // Redirection par défaut pour les routes inconnues
  {
    path: "*",
    component: () => <Navigate to="/index" replace />
  }
];

// Export des routes pour la navigation latérale (uniquement les routes protégées avec un menu)
export const sidebarRoutes = protectedRoutes.filter(route => route.name);

export { protectedRoutes, authRoutes };