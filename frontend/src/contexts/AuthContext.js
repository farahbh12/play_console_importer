// src/contexts/AuthContext.js
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import authService from '../services/auth';

// Création du contexte
export const AuthContext = createContext(null);

// Hook personnalisé pour utiliser le contexte
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth doit être utilisé à l\'intérieur d\'un AuthProvider');
  }
  return context;
};

// Fournisseur de contexte
export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Au lieu de gérer la navigation ici, nous allons retourner le chemin de redirection
  // et laisser le composant qui utilise le contexte gérer la navigation

  // Fonction pour forcer le rechargement de l'utilisateur
  const refreshUser = useCallback(async () => {
    try {
      setLoading(true);
      const user = await authService.getCurrentUser();
      setCurrentUser(user);
      setError(null);
      return user;
    } catch (err) {
      console.error('AuthContext: Erreur lors du chargement de l\'utilisateur:', err);
      setError(err.message || 'Erreur lors du chargement du profil');
      setCurrentUser(null);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Vérifier si l'utilisateur a un rôle spécifique
  const hasRole = useCallback((roles) => {
    return authService.hasRole(roles);
  }, []);

  // Vérifier si l'utilisateur est authentifié
  const isAuthenticated = useCallback(() => {
    return authService.isAuthenticated();
  }, []);

  // Charger l'utilisateur au démarrage
  useEffect(() => {
    const loadUser = async () => {
      try {
        const user = await authService.getCurrentUser();
        if (user) {
          setCurrentUser(user);
          setLoading(false);
        } else {
          setLoading(false);
        }
      } catch (error) {
        console.error('Erreur lors du chargement de l\'utilisateur:', error);
        setLoading(false);
      }
    };

    loadUser();
  }, []);

  // Fonction de connexion
  const login = async (email, password, userType = 'client') => {
    try {
      setLoading(true);
      setError(null);
      
      // Appel à authService.login avec le type d'utilisateur
      const user = await authService.login(email, password, userType);
      
      if (!user) {
        throw new Error('Aucune donnée utilisateur reçue');
      }
      
      // Mettre à jour l'état utilisateur
      setCurrentUser(user);
      setError(null);
      
      // Déterminer le chemin de redirection en fonction du rôle de l'utilisateur
      let redirectPath = '/';
      
      // Déterminer le rôle principal de l'utilisateur
      const userRole = user.role || user.user_type;
      console.log('Rôle utilisateur détecté:', userRole);
      
      // Déterminer le chemin de redirection
      if (user.is_superuser || userRole === 'administrateur' || 
          userRole === 'employee' || userRole === 'gestionnaire' || 
          userRole === 'admin' || userRole === 'manager') {
        // Tous les rôles admin/manager/employee
        redirectPath = '/admin/index';
      } else if (userRole === 'client' || userRole === 'Owner' || userRole === 'owner') {
        // Client et Owner (propriétaire client)
        redirectPath = '/client/dashboard';
      } else {
        // Par défaut, utiliser le type d'utilisateur de la connexion
        redirectPath = userType === 'client' ? '/client/dashboard' : '/admin/index';
        console.log('Utilisation du type de connexion pour la redirection:', userType);
      }
      
      console.log('Rôle utilisateur:', user.role, 'Redirection vers:', redirectPath);
      
      // Retourner les informations nécessaires pour la redirection
      return {
        user,
        redirectPath
      };
      
    } catch (err) {
      console.error('Erreur lors de la connexion:', err);
      
      // Nettoyer les données en cas d'erreur
      authService.logout();
      setCurrentUser(null);
      
      // Préparer un message d'erreur approprié
      let errorMessage = 'Échec de la connexion';
      
      if (err.response) {
        // Erreur de l'API
        const { status, data } = err.response;
        
        if (status === 400) {
          errorMessage = data.detail || 'Données de connexion invalides';
        } else if (status === 401) {
          errorMessage = 'Email ou mot de passe incorrect';
        } else if (status === 403) {
          errorMessage = 'Accès non autorisé';
        } else if (status >= 500) {
          errorMessage = 'Erreur du serveur. Veuillez réessayer plus tard.';
        }
      } else if (err.request) {
        // La requête a été faite mais aucune réponse n'a été reçue
        errorMessage = 'Impossible de se connecter au serveur. Vérifiez votre connexion Internet.';
      } else {
        // Une erreur s'est produite lors de la configuration de la requête
        errorMessage = err.message || 'Erreur lors de la connexion';
      }
      
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Fonction d'inscription
  const register = async (userData) => {
    try {
      console.log('AuthContext: Tentative d\'inscription pour:', userData);
      setLoading(true);
      setError(null);
      
      const result = await authService.register(userData);
      
      // Si l'inscription réussit, connecter l'utilisateur automatiquement
      if (result.user) {
        setCurrentUser(result.user);
      }
      
      return result;
    } catch (err) {
      console.error('AuthContext: Erreur lors de l\'inscription:', err);
      const errorMessage = err.message || 'Échec de l\'inscription. Veuillez réessayer.';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Fonction de déconnexion
  const logout = async () => {
    try {
      setLoading(true);
      await authService.logout();
      setCurrentUser(null);
      setError(null);
      
      // Retourner le chemin de redirection vers la page de connexion
      return {
        redirectPath: '/auth/login',
        options: { replace: true }
      };
    } catch (err) {
      console.error('AuthContext: Erreur lors de la déconnexion:', err);
      const errorMessage = err.message || 'Échec de la déconnexion. Veuillez réessayer.';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };
  
  // Valeur du contexte
  const value = {
    currentUser,
    loading,
    error,
    login,
    register,
    logout,
    refreshUser,
    hasRole,
    isAuthenticated,
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export default AuthContext;