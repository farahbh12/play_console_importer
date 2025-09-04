import React from 'react';
import { Navigate } from 'react-router-dom';

// --- Core Views ---
import Index from './views/Index.js';
import Profile from './views/examples/Profile.js';


// --- Auth Views ---
import Login from './views/examples/Login.js';
import Register from './views/examples/Register.js';
import ResetPassword from './views/examples/ResetPassword';
import PasswordResetRedirect from './views/examples/PasswordResetRedirect';
import AcceptInvitation from './views/examples/AcceptInvitation.js';
import Unauthorized from './views/Unauthorized';
import Assistant from './views/ai/Assistant';


// --- Admin Views ---
import ClientList from './views/examples/clientList';
import EmployeeList from './views/examples/employeeList';
import AdminProfileEdit from './views/examples/AdminProfileEdit';

// --- Client Views ---
import ClientProfileEdit from './views/examples/ClientProfileEdit';
import ManageTeam from './views/examples/ManageTeam';

// --- GCS Views ---
import DisplayGcsFiles from './views/gcs/DisplayGcsFiles';
import GcsConnectorPage from './views/gcs/GcsConnectorPage';
import ValidateGcsUri from './views/gcs/ValidateGcsUri';
import ValidationSuccess from './views/gcs/ValidationSuccess';
import DataSourceDetails from './views/gcs/DataSourceDetails';

// --- Subscription Views ---
import AbonnementList from './views/abonnements/AbonnementList';
import SubscriptionPage from './views/abonnements/SubscriptionPage';

// --- Hooks & Contexts ---
import { useAuth } from './contexts/AuthContext';

// Fonction pour obtenir le rôle de l'utilisateur
export const getUserRole = (user) => {
  if (!user) return 'guest';

  const role = user.role ? user.role.toUpperCase() : '';

  if (user.is_superuser || role === 'ADMIN' || role === 'ADMINISTRATEUR') {
    return 'admin';
  }
  if (role === 'MANAGER' || role === 'GESTIONNAIRE') {
    return 'manager';
  }
  // Détecter un compte employé même si le rôle n'est pas normalisé
  if (user.employee_profile || role === 'EMPLOYEE' || role === 'EMPLOYÉ' || user.is_staff === true) {
    return 'employee';
  }
  if (role === 'OWNER') {
    return 'owner';
  }
  if (role === 'MEMBRE_INVITE') {
    return 'membre_invite';
  }

  return 'guest'; // Default to guest if no role matches
};

// Fonction de vérification des rôles
const withRoleCheck = (Component, allowedRoles = []) => {
  return function ProtectedRoute(props) {
    const { currentUser } = useAuth();

    if (!currentUser) {
      return <Navigate to="/auth/login" replace />;
    }

    // Bloquer l'accès si le compte est désactivé côté backend
    if (currentUser.is_active === false) {
      return <Navigate to="/auth/unauthorized" replace />;
    }

    const userRole = getUserRole(currentUser);
    
    const canAccess = allowedRoles.length === 0 || 
                     allowedRoles.includes(userRole) ||
                     (userRole === 'manager' && allowedRoles.includes('admin'));
    
    if (!canAccess) {
      let redirectTo = '/auth/login';
      
      if (userRole === 'admin' || userRole === 'manager' || userRole === 'employee') {
        redirectTo = '/admin/index';
      } else if (userRole === 'client' || userRole === 'owner') {
        redirectTo = '/client/profile';
      } else if (userRole === 'membre_invite') {
        // Invited members: only allow /client/source and /client/destination
        redirectTo = '/client/profile';
      }
      
      return <Navigate to={redirectTo} replace />;
    }

    return <Component {...props} userRole={userRole} />;
  };
};

// Routes protégées (nécessitent une authentification)
const protectedRoutes = [
  // Admin & Manager Routes
  {
    path: '/admin/index',
    name: 'Tableau de bord',
    icon: 'ni ni-tv-2 text-primary',
    component: withRoleCheck(Index, ['admin', 'manager']),
    layout: '/admin',
    isIndex: true,
    invisible: true
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
    path: '/admin/clients',
    name: 'Gestion des clients',
    icon: 'ni ni-single-02 text-blue',
    component: withRoleCheck(ClientList, ['admin', 'manager']),
    layout: '/admin',
    section: 'Gestion'
  },
  {
    path: '/admin/AbonnementList',
    name: 'Gestion des abonnements',
    icon: 'ni ni-credit-card text-green',
    component: withRoleCheck(AbonnementList, ['admin', 'manager']),
    layout: '/admin',
    section: 'Gestion'
  },
  // Admin Only Routes
  {
    path: '/admin/employees',
    name: 'Gestion des employés',
    icon: 'ni ni-badge text-yellow',
    component: withRoleCheck(EmployeeList, ['admin']),
    layout: '/admin',
    section: 'Administration'
  },
  {
    path: '/admin/profile-edit',
    component: withRoleCheck(AdminProfileEdit, ['admin', 'manager', 'employee']),
    layout: '/admin',
    invisible: true
  },

  // Client (Owner & Invited Member) Routes
  // Redirect legacy client dashboard to /client/source
  {
    path: '/client/dashboard',
    component: () => <Navigate to="/client/profile" replace />,
    layout: '/client',
    invisible: true
  },
  {
    path: '/client/profile',
    name: 'Mon Profil',
    icon: 'ni ni-single-02 text-orange',
    component: withRoleCheck(Profile, ['owner', 'membre_invite']),
    layout: '/client',
    invisible: true
  },
  {
    path: '/client/profile-edit',
    component: withRoleCheck(ClientProfileEdit, ['owner']),
    layout: '/client',
    invisible: true
  },
  {
    path: '/client/source',
    name: 'Source',
    icon: 'ni ni-folder-17 text-cyan',
    component: withRoleCheck(DisplayGcsFiles, ['owner','membre_invite']),
    layout: '/client'
  },
  {
    path: '/client/AssistantAi',
    name: 'Assistant IA',
    icon: 'ni ni-atom text-purple',  // Icône atome (représente bien l’IA)
    component: withRoleCheck(Assistant, ['owner', 'membre_invite']),
    layout: '/client'
  },
  
  {
    path: '/client/destination',
    name: 'Destination',
    icon: 'ni ni-key-25 text-success',
    component: withRoleCheck(GcsConnectorPage, ['owner','membre_invite']),
    layout: '/client'
  },
  {
    path: '/client/validate-gcs-uri',
    component: withRoleCheck(ValidateGcsUri, ['owner']),
    layout: '/client',
    invisible: true
  },
  {
    path: '/client/validation-success',
    component: withRoleCheck(ValidationSuccess, ['owner']),
    layout: '/client',
    invisible: true
  },
  {
    path: '/client/data-source',
    name: 'Data Source',
    icon: 'ni ni-cloud-upload-96 text-blue',
    component: withRoleCheck(DataSourceDetails, ['owner']),
    layout: '/client'
  },
  {
    path: '/client/data-source-details/:id',
    component: withRoleCheck(DataSourceDetails, ['owner']),
    layout: '/client',
    invisible: true
  },
  {
    path: '/client/subscription',
    name: 'Abonnement',
    icon: 'ni ni-credit-card text-info',
    component: withRoleCheck(SubscriptionPage, ['owner']),
    layout: '/client'
  },
  {
    path: '/client/manage-team',
    name: 'Manage Team',
    icon: 'ni ni-settings-gear-65 text-purple',
    component: withRoleCheck(ManageTeam, ['owner']),
    layout: '/client'
  }
];

// Routes d'authentification (pas besoin d'authentification)
const authRoutes = [
  {
    path: "/login",
    name: "Login",
    component: Login,
    layout: "/auth",
  },
  {
    path: "/activation",
    name: "Accept Invitation",
    component: AcceptInvitation,
    layout: "/auth",
    invisible: true
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
    component: () => <Navigate to="/client/profile" replace />
  }
];

// Export des routes pour la navigation latérale (uniquement les routes protégées avec un menu)
export const sidebarRoutes = protectedRoutes.filter(route => route.name && !route.invisible);

export { protectedRoutes, authRoutes };