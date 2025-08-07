// src/services/clientService.js
import api from './api';
import authService from '../services/auth';

const clientService = {
  // Récupérer le client actuel
  getCurrent: async () => {
    try {
      const user = authService.getCurrentUser();
      if (!user) {
        throw new Error('Aucun utilisateur connecté');
      }
      
      const response = await api.get(`clients/${user.id}/`);
      return response.data;
    } catch (error) {
      console.error('Error fetching current client:', error);
      throw error;
    }
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
};

export default clientService;