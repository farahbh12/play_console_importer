// src/services/abonnementService.js
import api from './api';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const abonnementService = {
  /**
   * Récupère tous les abonnements
   */
  getAll: async () => {
    try {
      const response = await api.get(`${API_BASE_URL}/abonnements/`);
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la récupération des abonnements:', error);
      throw error;
    }
  },

  // Souscrire à un abonnement
  souscrireAbonnement: async (subscriptionData) => {
    try {
      const response = await api.post('/client/subscribe/', subscriptionData);
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la souscription:', error);
      throw error.response?.data || { 
        message: error.message || 'Une erreur est survenue lors de la souscription' 
      };
    }
  },
  /**
   * Met à jour un abonnement existant
   */
  update: async (id, data) => {
    try {
      const response = await api.put(
        `${API_BASE_URL}/abonnements/${id}/update/`, 
        data
      );
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la mise à jour de l\'abonnement:', error);
      throw error.response?.data || { message: 'Erreur lors de la mise à jour de l\'abonnement' };
    }
  },

  /**
   * Active/désactive un abonnement
   */
  toggle: async (id) => {
    try {
      const response = await api.patch(
        `${API_BASE_URL}/abonnements/${id}/toggle/`
      );
      return response.data;
    } catch (error) {
      console.error('Erreur lors du changement d\'état de l\'abonnement:', error);
      throw error.response?.data || { message: 'Erreur lors du changement d\'état de l\'abonnement' };
    }
  },

  /**
   * Récupère un abonnement par son ID
   */
  getById: async (id) => {
    try {
      const response = await api.get(`${API_BASE_URL}/abonnements/${id}/`);
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la récupération de l\'abonnement:', error);
      throw error;
    }
  }
};

export default abonnementService;