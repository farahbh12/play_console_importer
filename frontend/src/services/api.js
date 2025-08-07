// src/services/api.js
import axios from 'axios';
import { toast } from 'react-toastify';
import authService from './auth';

// Configuration de base de l'API
const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  }
});

// Variables pour gérer le rafraîchissement du token
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Intercepteur pour ajouter le token JWT à chaque requête
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Gestion des erreurs et rafraîchissement du token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Si l'erreur est 401 et que ce n'est pas une tentative de rafraîchissement
    if (error.response?.status === 401 && !originalRequest._retry) {
      // Si on est déjà en train de rafraîchir le token, on met en file d'attente
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
        .then(token => {
          originalRequest.headers['Authorization'] = `Bearer ${token}`;
          return api(originalRequest);
        })
        .catch(err => {
          return Promise.reject(err);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshToken = localStorage.getItem('refresh');
        if (!refreshToken) {
          authService.logout();
          return Promise.reject(error);
        }

        // Rafraîchir le token
        const response = await axios.post(
          'http://localhost:8000/token/refresh/',
          { refresh: refreshToken }
        );

        const { access } = response.data;
        
        // Mettre à jour le token
        localStorage.setItem('token', access);
        api.defaults.headers.common['Authorization'] = `Bearer ${access}`;
        
        // Mettre à jour la requête originale
        originalRequest.headers['Authorization'] = `Bearer ${access}`;
        
        // Traiter les requêtes en attente
        processQueue(null, access);
        
        // Renvoyer la requête originale
        return api(originalRequest);
      } catch (refreshError) {
        // En cas d'échec du rafraîchissement, déconnecter l'utilisateur
        processQueue(refreshError, null);
        authService.logout();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // Gestion des autres erreurs
    if (error.response) {
      // Erreur 403 - Accès refusé
      if (error.response.status === 403) {
        toast.error("Accès refusé. Vous n'avez pas les droits nécessaires.");
      }
      // Erreur 404 - Non trouvé
      else if (error.response.status === 404) {
        console.error('Ressource non trouvée:', error.config.url);
      }
      // Erreur 500+ - Erreur serveur
      else if (error.response.status >= 500) {
        toast.error('Erreur serveur. Veuillez réessayer plus tard.');
      }
    } else if (error.request) {
      // La requête a été faite mais aucune réponse n'a été reçue
      toast.error('Impossible de se connecter au serveur. Vérifiez votre connexion internet.');
    } else {
      // Erreur lors de la configuration de la requête
      console.error('Erreur de configuration:', error.message);
    }
    
    return Promise.reject(error);
  }
);

export default api;