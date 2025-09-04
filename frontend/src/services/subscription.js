import api from './api';

const subscriptionService = {
  /**
   * Récupère les informations d'abonnement d'un client
   * @param {number} clientId - L'ID du client
   * @returns {Promise<Object>} Les informations d'abonnement du client
   */
  getClientSubscription: async (clientId) => {
    try {
      const response = await api.get(`/clients/${clientId}/subscription/`);
      return response.data;
    } catch (error) {
      console.error('Error fetching client subscription:', error);
      if (error.response?.status === 404) {
        return null; // Aucun abonnement trouvé
      }
      throw error;
    }
  },

  /**
   * Vérifie si un client a un abonnement actif
   * @param {number} clientId - L'ID du client
   * @returns {Promise<Object>} Les informations d'abonnement du client
   */
  checkSubscriptionStatus: async (clientId) => {
    try {
      const response = await api.get(`/api/client/${clientId}/subscription-status/`);
      return response.data;
    } catch (error) {
      console.error('Error checking subscription status:', error);
      throw error;
    }
  },

  /**
   * Récupère la liste de tous les abonnements disponibles
   * @returns {Promise<Array>} La liste des abonnements
   */
  getAvailableSubscriptions: async () => {
    try {
      const response = await api.get('/api/subscriptions/');
      return response.data;
    } catch (error) {
      console.error('Error fetching available subscriptions:', error);
      throw error;
    }
  },

  /**
   * Met à jour l'abonnement d'un client
   * @param {number} clientId - L'ID du client
   * @param {string} subscriptionId - L'ID du nouvel abonnement
   * @returns {Promise<Object>} La réponse du serveur
   */
  updateClientSubscription: async (clientId, subscriptionId) => {
    try {
      const response = await api.post(`/api/client/subscribe/`, {
        client_id: clientId,
        subscription_id: subscriptionId
      });
      return response.data;
    } catch (error) {
      console.error('Error updating client subscription:', error);
      throw error;
    }
  },

  /**
   * Envoie une demande de changement d'abonnement
   * @param {number} clientId - L'ID du client
   * @param {string} newPlanId - L'ID du nouveau forfait demandé
   * @param {string} reason - La raison du changement
   * @returns {Promise<Object>} La réponse du serveur
   */
  /**
   * Envoie une demande de changement d'abonnement
   * @param {number} clientId - L'ID du client
   * @param {string} newPlanId - L'ID du nouveau forfait demandé
   * @param {string} reason - La raison du changement
   * @returns {Promise<Object>} La réponse du serveur
   */
  requestSubscriptionChange: async (clientId, newPlanId, reason = '') => {
    try {
      const response = await api.post(`/api/client/${clientId}/subscription-change-request/`, {
        plan_id: newPlanId,
        reason: reason,
        request_date: new Date().toISOString()
      });
      
      return response.data;
    } catch (error) {
      console.error('Error requesting subscription change:', error);
      
      // Improve error messages
      let errorMessage = 'Une erreur est survenue lors de la demande de changement';
      if (error.response) {
        if (error.response.status === 400) {
          errorMessage = error.response.data.error || errorMessage;
        } else if (error.response.status === 403) {
          errorMessage = 'Vous n\'êtes pas autorisé à effectuer cette action';
        } else if (error.response.status === 404) {
          errorMessage = 'Client ou forfait introuvable';
        } else if (error.response.status === 409) {
          errorMessage = 'Une demande de changement est déjà en cours pour ce client';
        }
      }
      
      const enhancedError = new Error(errorMessage);
      enhancedError.response = error.response;
      throw enhancedError;
    }
  },

  /**
   * Annule une demande de changement d'abonnement en attente
   * @param {number} requestId - L'ID de la demande à annuler
   * @returns {Promise<Object>} La réponse du serveur
   */
  cancelSubscriptionChangeRequest: async (requestId) => {
    try {
      const response = await api.delete(`/api/subscription-change-requests/${requestId}/`);
      return response.data;
    } catch (error) {
      console.error('Error canceling subscription change request:', error);
      
      let errorMessage = 'Une erreur est survenue lors de l\'annulation de la demande';
      if (error.response) {
        if (error.response.status === 404) {
          errorMessage = 'Demande introuvable ou déjà traitée';
        } else if (error.response.status === 403) {
          errorMessage = 'Vous n\'êtes pas autorisé à annuler cette demande';
        } else if (error.response.status === 400) {
          errorMessage = error.response.data.error || errorMessage;
        }
      }
      
      const enhancedError = new Error(errorMessage);
      enhancedError.response = error.response;
      throw enhancedError;
    }
  },

  /**
   * Récupère l'historique des demandes de changement d'abonnement pour un client
   * @param {number} clientId - L'ID du client
   * @param {Object} options - Options de filtrage et de pagination
   * @param {number} [options.limit=10] - Nombre maximum de résultats à retourner
   * @param {number} [options.offset=0] - Nombre d'éléments à sauter
   * @param {string} [options.status] - Filtrer par statut (pending, approved, rejected, cancelled)
   * @returns {Promise<{count: number, results: Array}>} La liste paginée des demandes de changement
   */
  getSubscriptionChangeHistory: async (clientId, { limit = 10, offset = 0, status } = {}) => {
    try {
      const params = { limit, offset };
      if (status) params.status = status;
      
      const response = await api.get(`/api/client/${clientId}/subscription-change-history/`, { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching subscription change history:', error);
      
      let errorMessage = 'Impossible de charger l\'historique des demandes';
      if (error.response) {
        if (error.response.status === 404) {
          errorMessage = 'Client introuvable';
        } else if (error.response.status === 403) {
          errorMessage = 'Vous n\'êtes pas autorisé à consulter cet historique';
        } else if (error.response.status === 400) {
          errorMessage = error.response.data.error || errorMessage;
        }
      }
      
      const enhancedError = new Error(errorMessage);
      enhancedError.response = error.response;
      throw enhancedError;
    }
  }
};

export default subscriptionService;
