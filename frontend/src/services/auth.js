// src/services/auth.js
import api from './api';





// Helper to set tokens in storage and axios
const setSession = (access, refresh) => {
  if (access) {
    localStorage.setItem('token', access);
    localStorage.setItem('access_token', access);
    api.defaults.headers.common['Authorization'] = `Bearer ${access}`;
  }
  if (refresh) {
    localStorage.setItem('refresh', refresh);
    localStorage.setItem('refresh_token', refresh);
  }
};

// Helper to set user in storage
const setUser = (user) => {
  if (user) {
    localStorage.setItem('user', JSON.stringify(user));
  } else {
    localStorage.removeItem('user');
  }
};

// Clear session without redirect
const clearSession = () => {
  try {
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    localStorage.removeItem('refresh');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    delete api.defaults.headers.common['Authorization'];
  } catch (_) {}
};
/**
 * Effectue une tentative de connexion
 * @param {string} email - L'email de l'utilisateur
 * @param {string} password - Le mot de passe
 * @param {string} userType - Le type d'utilisateur ('client' ou 'employee')
 * @returns {Promise<Object>} Les données de l'utilisateur connecté
 */
const login = async (email, password, userType = 'client') => {
  try {
    const cleanEmail = (email || '').trim();
    const cleanPassword = password || '';
    
    if (!cleanEmail || !cleanPassword) {
      throw new Error('Veuillez remplir tous les champs obligatoires');
    }
    
    const endpoint = userType === 'employee' ? '/employee/login/' : '/client/login/';
    const requestData = { email: cleanEmail, password: cleanPassword };
    
    const response = await api.post(endpoint, requestData, {
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });
    
    const { access, refresh, user } = response.data;
    
    if (!access || !user) {
      throw new Error('Réponse du serveur incomplète');
    }
    
    localStorage.setItem('token', access);
    localStorage.setItem('user', JSON.stringify(user)); // Stocker les données utilisateur
    if (refresh) {
      localStorage.setItem('refresh', refresh);
    }
    
    const userData = {
      ...user,
      user_type: userType
    };
    
    setUser(userData);
    
    return userData;
    
  } catch (error) {
    if (error.response?.data) {
      const { data } = error.response;
      
      if (data.non_field_errors) {
        throw new Error(data.non_field_errors.join(' '));
      } else if (data.detail) {
        throw new Error(data.detail);
      } else if (typeof data === 'object') {
        const firstError = Object.values(data)[0];
        if (Array.isArray(firstError)) {
          throw new Error(firstError[0]);
        } else if (typeof firstError === 'string') {
          throw new Error(firstError);
        }
      }
    }
    
    if (error.message) {
      throw error;
    }
    
    throw new Error('Erreur lors de la connexion');
  }
};

/**
 * Enregistre un nouvel utilisateur
 * @param {Object} userData - Les données de l'utilisateur à enregistrer
 * @returns {Promise<Object>} La réponse du serveur
 */
const register = async (userData) => {
  try {
    const response = await api.post('/auth/client/register/', userData);
    return response.data;
  } catch (error) {
    console.error('Erreur d\'inscription:', error);
    let errorMessage = "Erreur lors de l'inscription. Veuillez réessayer.";

    if (error.response?.data) {
      const { data } = error.response;
      if (typeof data === 'object') {
        const errorMessages = Object.entries(data)
          .map(([field, errors]) => {
            const errorList = Array.isArray(errors) ? errors.join(', ') : errors;
            return `${field}: ${errorList}`;
          })
          .join('\n');
        errorMessage = errorMessages || errorMessage;
      } else if (typeof data === 'string') {
        errorMessage = data;
      }
    } else if (error.request) {
      errorMessage = "Impossible de se connecter au serveur. Vérifiez votre connexion internet.";
    }

    throw new Error(errorMessage);
  }
};

/**
 * Récupère l'utilisateur actuellement connecté
 * @returns {Object|null} L'utilisateur connecté ou null si non connecté
 */
const getCurrentUser = () => {
  const userStr = localStorage.getItem('user');
  const token = localStorage.getItem('token');
  
  if (!userStr || !token) {
    return null;
  }
  
  try {
    const user = JSON.parse(userStr);
    // Vérification basique de la structure de l'utilisateur
    if (user && user.id && user.email) {
      // Mettre à jour l'en-tête d'autorisation
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      return user;
    }
    return null;
  } catch (error) {
    console.error('Erreur lors du parsing des données utilisateur:', error);
    return null;
  }
};

/**
 * Vérifie si l'utilisateur est authentifié
 * @returns {boolean} True si l'utilisateur est authentifié, false sinon
 */
const isAuthenticated = () => {
  return !!getCurrentUser();
};

/**
 * Vérifie si l'utilisateur a un rôle spécifique
 * @param {string|Array<string>} roles - Le ou les rôles à vérifier
 * @returns {boolean} True si l'utilisateur a le rôle, false sinon
 */
const hasRole = (roles) => {
  const user = getCurrentUser();
  if (!user) return false;
  
  // Définir les rôles de l'utilisateur
  const userRoles = [];
  
  // Normaliser le rôle en minuscules pour la comparaison
  const userRole = user.role ? user.role.toLowerCase() : '';
  
  // Ajouter le rôle selon le type d'utilisateur
  if (user.is_superuser || userRole === 'administrateur' || userRole === 'admin') {
    userRoles.push('admin');
  } else if (userRole === 'gestionnaire' || userRole === 'manager') {
    userRoles.push('manager');
  } else if (userRole === 'client' || userRole === 'owner') {
    userRoles.push('client');
  }
  
  // Ajouter le type d'utilisateur (employee ou client)
  if (user.user_type) {
    userRoles.push(user.user_type);
  }
  
  // Ajouter le rôle brut pour la rétrocompatibilité
  if (user.role) {
    userRoles.push(user.role);
  }
  
  console.log('Vérification des rôles:', {
    user,
    userRoles,
    requiredRoles: Array.isArray(roles) ? roles : [roles]
  });
  
  const requiredRoles = Array.isArray(roles) ? roles : [roles];
  return requiredRoles.some(role => userRoles.includes(role));
};

/**
 * Déconnecte l'utilisateur
 */
const logout = () => {
  // Supprimer les informations d'authentification
  clearSession();
  
  // Rediriger vers la page de connexion
  window.location.href = '/auth/login';
};

const authService = {
  login,
  register,
  logout,
  getCurrentUser,
  isAuthenticated,
  hasRole,
  setSession,
  setUser,
  clearSession
};

export default authService;