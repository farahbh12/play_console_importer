import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import AdminSidebar from './AdminSidebar';
import ManagerSidebar from './ManagerSidebar';
import ClientSidebar from './ClientSidebar';

const getUserRole = (user) => {
  if (!user) return 'guest';
  
  // Vérifier d'abord le type d'utilisateur (user_type) s'il est défini
  if (user.user_type) {
    const userType = user.user_type.toLowerCase();
    if (userType === 'employee') return 'employee';
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
      return 'employee';
    }
    if (userRole === 'client' || userRole === 'owner' || userRole === 'membre_invite') {
      return 'client';
    }
  }
  
  // Vérifier si l'utilisateur a un employee_id (pour la rétrocompatibilité)
  if (user.employee_id) {
    return 'employee';
  }
  
  // Par défaut, considérer comme client
  return 'client';
};

const SidebarSwitcher = ({ routes, logo, forceSidebar }) => {
  const { currentUser } = useAuth();

  if (!currentUser) {
    return null;
  }

  let userRole = getUserRole(currentUser);
  console.log('Rôle détecté dans SidebarSwitcher:', userRole, currentUser);

  if (forceSidebar) {
    userRole = forceSidebar;
  }

  // Les employés utilisent la barre latérale admin
  if (userRole === 'employee') {
    userRole = 'admin';
  }

  switch (userRole) {
    case 'admin':
      return <AdminSidebar routes={routes} logo={logo} user={currentUser} />;
    case 'manager':
      return <ManagerSidebar routes={routes} logo={logo} user={currentUser} />;
    case 'client':
    default:
      return <ClientSidebar routes={routes} logo={logo} user={currentUser} />;
  }
};

export default SidebarSwitcher;
