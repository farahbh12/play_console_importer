import api from './api';

const subscriptionService = {
  // Envoyer une demande de changement d'abonnement
  requestSubscriptionChange: async (data) => {
    try {
      const response = await api.post('/api/subscription/change-request/', data);
      return response.data;
    } catch (error) {
      console.error('Error requesting subscription change:', error);
      throw error;
    }
  },

  // Récupérer l'abonnement actuel de l'utilisateur
  getCurrentSubscription: async () => {
    try {
      const response = await api.get('/api/subscription/current/');
      return response.data;
    } catch (error) {
      console.error('Error fetching current subscription:', error);
      throw error;
    }
  },

  // Récupérer l'historique des demandes de changement
  getChangeRequests: async () => {
    try {
      const response = await api.get('/api/subscription/change-requests/');
      return response.data;
    } catch (error) {
      console.error('Error fetching change requests:', error);
      throw error;
    }
  },

  // Mettre à jour le statut d'une demande (admin uniquement)
  updateRequestStatus: async (requestId, status) => {
    try {
      const response = await api.put(`/api/subscription/change-requests/${requestId}/`, { status });
      return response.data;
    } catch (error) {
      console.error('Error updating request status:', error);
      throw error;
    }
  }
};

export default subscriptionService;
