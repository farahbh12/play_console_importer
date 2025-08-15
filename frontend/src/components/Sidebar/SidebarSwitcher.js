import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import AdminSidebar from './AdminSidebar';
import ManagerSidebar from './ManagerSidebar';
import ClientSidebar from './ClientSidebar';

const getUserRole = (user) => {
  if (!user) return 'guest';
  const userRole = user.role ? user.role.toLowerCase() : '';

  if (user.is_superuser || userRole === 'admin' || userRole === 'administrateur') {
    return 'admin';
  }
  if (userRole === 'manager' || userRole === 'gestionnaire') {
    return 'manager';
  }
  if (userRole === 'client' || userRole === 'owner' || userRole === 'membre_invite') {
    return 'client';
  }
  return 'guest';
};

const SidebarSwitcher = ({ routes, logo, forceSidebar }) => {
  const { currentUser } = useAuth();

  if (!currentUser) {
    return null;
  }

  let userRole = getUserRole(currentUser);

  if (forceSidebar) {
    userRole = forceSidebar;
  }

  switch (userRole) {
    case 'admin':
      return <AdminSidebar routes={routes} logo={logo} />;
    case 'manager':
      return <ManagerSidebar routes={routes} logo={logo} />;
    case 'client':
    default:
      return <ClientSidebar user={currentUser} />;
  }
};

export default SidebarSwitcher;
