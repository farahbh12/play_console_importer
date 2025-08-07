// Configuration de l'application
const config = {
  // URL de base de l'API Django
  API_BASE_URL: 'http://localhost:8000',
  
  // Chemins des endpoints d'authentification
  AUTH_ENDPOINTS: {
    LOGIN: '/token/',
    REFRESH: '/token/refresh/',
    CLIENT_REGISTER: '/client/register/',
    CLIENT_LOGIN: '/client/login/',
    EMPLOYEE_REGISTER: '/employee/register/',
    EMPLOYEE_LOGIN: '/employee/login/',
    PASSWORD_RESET: '/password-reset/',
    PASSWORD_RESET_CONFIRM: '/password-reset-confirm/'
  },
  
  // Rôles des utilisateurs
  ROLES: {
    ADMIN: 'admin',
    MANAGER: 'manager',
    EMPLOYEE: 'employee',
    CLIENT: 'client'
  },
  
  // Chemins des routes de l'application
  ROUTES: {
    HOME: '/',
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    FORGOT_PASSWORD: '/auth/forgot-password',
    ADMIN_DASHBOARD: '/admin/dashboard',
    EMPLOYEE_DASHBOARD: '/employee/dashboard',
    CLIENT_DASHBOARD: '/client/dashboard'
  }
};

export default config;
