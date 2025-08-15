import axios from 'axios';
import { toast } from 'react-toastify';

// Cette fonction est séparée pour être appelée par l'intercepteur
// et éviter les dépendances circulaires avec authService.
const refreshToken = async () => {
    try {
        const refresh = localStorage.getItem('refresh_token');
        if (!refresh) throw new Error("No refresh token available");

        const response = await axios.post('http://127.0.0.1:8000/api/token/refresh/', { refresh });
        
        if (response.data.access) {
            localStorage.setItem('access_token', response.data.access);
            return response.data;
        }
        return null; // Retourne null si le token n'est pas rafraîchi
    } catch (error) {
        console.error("Failed to refresh token", error);
        // Nettoyer le stockage local et rediriger vers la page de connexion
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        // Rediriger seulement si on n'est pas déjà sur une page d'authentification
        if (!window.location.pathname.startsWith('/auth')) {
            window.location.href = '/auth/login';
        }
        return null;
    }
};

// 1. Configuration de base d'Axios
const api = axios.create({
  baseURL: 'http://127.0.0.1:8000', // Assure que toutes les requêtes pointent vers le backend
  headers: {
    'Content-Type': 'application/json',
  }
});

// 2. Intercepteur pour ajouter le token JWT à chaque requête
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 3. Gestion des erreurs et rafraîchissement du token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    const publicUrls = [
      '/api/team/check-invitation',
      '/api/team/verify-invitation',
      '/api/token/', // JWT token login
      '/client/login/', // application login (client)
      '/employee/login/' // application login (employee)
    ];

    // Si l'URL n'est pas publique et que l'erreur est 401, on tente de rafraîchir
    if (error.response.status === 401 && !originalRequest._retry && !publicUrls.some(url => originalRequest.url.includes(url))) {
      originalRequest._retry = true; // Marquer comme nouvelle tentative

      const newTokens = await refreshToken();
      if (newTokens && newTokens.access) {
        // Mettre à jour le token et rejouer la requête originale
        originalRequest.headers['Authorization'] = `Bearer ${newTokens.access}`;
        return api(originalRequest);
      }
    }

    // Gérer les erreurs serveur génériques
    if (error.response && error.response.status >= 500) {
      toast.error("Une erreur serveur s'est produite. Veuillez réessayer plus tard.");
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