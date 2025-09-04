import api from './api';
import authService from './auth';

const API_BASE_URL = '/api/employees/';

const employeeService = {
  // ✅ Récupérer l'employé actuel via l'ID de l'utilisateur connecté
  getCurrent: async () => {
    try {
      // Récupérer l'utilisateur de manière asynchrone
      const user = await authService.getCurrentUser();
      
      if (!user || !user.id) {
        console.log('Aucun utilisateur connecté ou ID manquant');
        throw new Error('Utilisateur non connecté');
      }
      
      console.log('Récupération des données employé pour user_id:', user.id);
      
      // Récupérer la liste des employés avec le filtre user_id
      const response = await api.get(`employees/?user_id=${user.id}`);
      
      if (!response.data || response.data.length === 0) {
        console.log('Aucun employé trouvé pour user_id:', user.id);
        throw new Error('Aucun employé trouvé pour cet utilisateur');
      }
      
      console.log('Données employé récupérées:', response.data[0]);
      
      // Retourner le premier employé trouvé avec les données utilisateur fusionnées
      return {
        ...response.data[0],
        user: user // Inclure les données utilisateur complètes
      };
    } catch (error) {
      console.error("Erreur lors de la récupération de l'employé:", error);
      throw error;
    }
  }
  ,

  // ✅ Liste complète des employés
  getAll: async (params = {}) => {
    try {
      const response = await api.get(API_BASE_URL, { params });
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la récupération des employés:', error);
      
      // Gestion plus robuste des erreurs
      if (error.response) {
        // La requête a été faite et le serveur a répondu avec un code d'erreur
        throw new Error(`Erreur du serveur: ${error.response.status} - ${error.response.statusText}`);
      } else if (error.request) {
        // La requête a été faite mais aucune réponse n'a été reçue
        throw new Error('Aucune réponse du serveur. Vérifiez votre connexion.');
      } else {
        // Une erreur s'est produite lors de la configuration de la requête
        throw new Error(`Erreur lors de la configuration de la requête: ${error.message}`);
      }
    }
  },

  // ✅ Détails d'un employé par son ID
  getDetails: async (employeeId) => {
    try {
      const response = await api.get(`${API_BASE_URL}${employeeId}/`);
      return response.data;
    } catch (error) {
      console.error("Erreur lors de la récupération des détails de l'employé:", error);
      
      // Gestion plus robuste des erreurs
      if (error.response) {
        // La requête a été faite et le serveur a répondu avec un code d'erreur
        if (error.response.status === 404) {
          throw new Error(`Profil employé non trouvé. Vérifiez que l'utilisateur a un profil employé associé.`);
        }
        // Autres erreurs de réponse
        throw new Error(`Erreur du serveur: ${error.response.status} - ${error.response.statusText}`);
      } else if (error.request) {
        // La requête a été faite mais aucune réponse n'a été reçue
        throw new Error('Aucune réponse du serveur. Vérifiez votre connexion.');
      } else {
        // Une erreur s'est produite lors de la configuration de la requête
        throw new Error(`Erreur lors de la configuration de la requête: ${error.message}`);
      }
    }
  },

  // ✅ Mise à jour d'un employé
  update: async (employeeId, data) => {
    try {
      // Correction de l'URL : suppression du /update/ final pour suivre la convention REST
      const response = await api.put(`${API_BASE_URL}${employeeId}/`, data);
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la mise à jour de l\'employé:', error);
      
      // Gestion plus robuste des erreurs
      if (error.response) {
        // La requête a été faite et le serveur a répondu avec un code d'erreur
        throw new Error(`Erreur du serveur: ${error.response.status} - ${error.response.statusText}`);
      } else if (error.request) {
        // La requête a été faite mais aucune réponse n'a été reçue
        throw new Error('Aucune réponse du serveur. Vérifiez votre connexion.');
      } else {
        // Une erreur s'est produite lors de la configuration de la requête
        throw new Error(`Erreur lors de la configuration de la requête: ${error.message}`);
      }
    }
  },

  // ✅ Désactiver un employé
  deactivate: async (employeeId) => {
    try {
      const response = await api.patch(
        `${API_BASE_URL}${employeeId}/deactivate/`
      );
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la désactivation:', error);
      
      // Gestion plus robuste des erreurs
      if (error.response) {
        // La requête a été faite et le serveur a répondu avec un code d'erreur
        throw new Error(`Erreur du serveur: ${error.response.status} - ${error.response.statusText}`);
      } else if (error.request) {
        // La requête a été faite mais aucune réponse n'a été reçue
        throw new Error('Aucune réponse du serveur. Vérifiez votre connexion.');
      } else {
        // Une erreur s'est produite lors de la configuration de la requête
        throw new Error(`Erreur lors de la configuration de la requête: ${error.message}`);
      }
    }
  },

  // ✅ Réactiver un employé
  activate: async (employeeId) => {
    try {
      const response = await api.patch(
        `${API_BASE_URL}${employeeId}/activate/`
      );
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la réactivation:', error);
      
      // Gestion plus robuste des erreurs
      if (error.response) {
        // La requête a été faite et le serveur a répondu avec un code d'erreur
        throw new Error(`Erreur du serveur: ${error.response.status} - ${error.response.statusText}`);
      } else if (error.request) {
        // La requête a été faite mais aucune réponse n'a été reçue
        throw new Error('Aucune réponse du serveur. Vérifiez votre connexion.');
      } else {
        // Une erreur s'est produite lors de la configuration de la requête
        throw new Error(`Erreur lors de la configuration de la requête: ${error.message}`);
      }
    }
  }
};

export default employeeService;