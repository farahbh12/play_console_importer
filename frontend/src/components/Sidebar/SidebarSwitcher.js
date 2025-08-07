import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { getUserRole } from '../../routes';
import AdminSidebar from './AdminSidebar';
import ManagerSidebar from './ManagerSidebar';
import ClientSidebar from './ClientSidebar';

const SidebarSwitcher = ({ forceSidebar }) => {
  const { currentUser } = useAuth();

  if (!currentUser) {
    return null;
  }

  // Déterminer le type d'utilisateur en utilisant la fonction getUserRole
  const getUserType = () => {
    // Utiliser la fonction getUserRole pour une détection cohérente des rôles
    const userRole = getUserRole(currentUser);
    
    console.log('SidebarSwitcher - Détection du rôle utilisateur:', {
      is_superuser: currentUser.is_superuser,
      role: currentUser.role,
      user_type: currentUser.user_type,
      employee_id: currentUser.employee_id,
      detectedRole: userRole
    });
    
    console.log(`→ Rôle détecté: ${userRole}`);
    return userRole;
  };

  // Utiliser forceSidebar si fourni, sinon déterminer automatiquement
  const sidebarType = forceSidebar || getUserType();
  console.log('Type de sidebar à afficher:', sidebarType, '(forcé:', !!forceSidebar, ')');

  // Rendre la barre latérale appropriée
  switch (sidebarType) {
    case 'admin':
      return <AdminSidebar user={currentUser} />;
    case 'manager':
      return <ManagerSidebar user={currentUser} />;
    case 'client':
    default:
      return <ClientSidebar user={currentUser} />;
  }
};

export default SidebarSwitcher;
