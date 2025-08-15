// src/services/clientService.js
import api from './api';
import authService from '../services/auth';

const clientService = {
  // Récupérer le client actuel
  getCurrent() {
    const user = authService.getCurrentUser();
    if (!user) {
      return Promise.reject(new Error('Utilisateur non trouvé'));
    }

    // Déduire l'identifiant Client attendu par l'API
    const clientId = user.client_id || user.clientId || user.client?.id;
    if (clientId) {
      return api.get(`/clients/${clientId}/`).then(res => res.data);
    }

    // Fallback: utiliser l'ID UTILISATEUR (le backend résout par user_id)
    const userId = user.id || user.user?.id;
    if (userId) {
      return api.get(`/clients/${userId}/`).then(res => res.data);
    }

    return Promise.reject(new Error("Identifiant client introuvable dans l'objet utilisateur (client_id) et aucun user_id disponible."));
  },

  // Récupérer la liste des clients
  getAll: async (params = {}) => {
    try {
      const response = await api.get('clients/', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching clients:', error);
      throw error;
    }
  },

  // Récupérer les détails d'un client spécifique
  getDetails: async (clientId) => {
    try {
      const response = await api.get(`clients/${clientId}/`);
      return response.data;
    } catch (error) {
      console.error('Error fetching client details:', error);
      throw error;
    }
  },

  // Mettre à jour un client
  update: async (clientId, data) => {
    try {
      console.log('Sending update request to:', `clients/${clientId}/update/`);
      console.log('Data being sent:', data);
      const response = await api.put(`clients/${clientId}/update/`, data);
      return response.data;
    } catch (error) {
      console.error('Error updating client:', error);
      console.error('Error details:', error.response?.data);
      throw error;
    }
  },

  // Met à jour le statut (actif/inactif) d'un client
  setStatus: async (userId, isActive) => {
    try {
      const endpoint = isActive 
        ? `clients/${userId}/activate/` 
        : `clients/${userId}/deactivate/`;
      
      const response = await api.patch(endpoint);
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la mise à jour du statut du client:', error);
      throw error;
    }
  },

  // Changer l'abonnement d'un client (par user_id) vers un type donné
  changeAbonnement: async (userId, type_abonnement) => {
    try {
      const response = await api.post(`clients/${userId}/change-abonnement/`, { type_abonnement });
      return response.data;
    } catch (error) {
      console.error("Erreur lors du changement d'abonnement du client:", error);
      throw error.response?.data || { message: "Erreur lors du changement d'abonnement" };
    }
  },
};

export default clientService;