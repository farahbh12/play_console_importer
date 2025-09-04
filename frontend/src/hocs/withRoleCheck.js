import React from 'react';
import { Navigate } from 'react-router-dom';

export const withRoleCheck = (WrappedComponent, allowedRoles = []) => {
  const WithRoleCheck = (props) => {
    const { currentUser } = props;

    if (!currentUser) {
      return <Navigate to="/auth/login" replace />;
    }

    if (currentUser.is_active === false) {
      return <Navigate to="/auth/unauthorized" replace />;
    }

    const userRole = (currentUser.role || '').toLowerCase();
    
    const canAccess = allowedRoles.length === 0 || 
                     allowedRoles.includes(userRole) ||
                     (userRole === 'manager' && allowedRoles.includes('admin'));
    
    if (!canAccess) {
      let redirectTo = '/auth/login';
      
      if (['admin', 'manager', 'employee'].includes(userRole)) {
        redirectTo = '/admin/profile';
      } else if (['client', 'owner'].includes(userRole)) {
        const hasTenant = currentUser?.tenant_id || (currentUser?.tenant && currentUser.tenant.id);
        redirectTo = hasTenant ? '/client/profile' : '/client/subscription?firstLogin=true';
      } else if (userRole === 'membre_invite') {
        redirectTo = '/client/profile';
      }
      
      return <Navigate to={redirectTo} replace />;
    }

    return <WrappedComponent {...props} userRole={userRole} />;
  };

  // Copy display name for better debugging
  WithRoleCheck.displayName = `withRoleCheck(${WrappedComponent.displayName || WrappedComponent.name || 'Component'})`;
  
  return WithRoleCheck;
};

export default withRoleCheck;
