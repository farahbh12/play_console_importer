import api from './api';
import config from '../config';

const authService = {
  // Demander une réinitialisation de mot de passe
  requestPasswordReset: async (email) => {
    try {
      const response = await api.post(config.AUTH_ENDPOINTS.PASSWORD_RESET, { email });
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la demande de réinitialisation:', error.response?.data || error.message);
      throw error.response?.data || new Error('Une erreur est survenue.');
    }
  },

  // Confirmer la réinitialisation du mot de passe
  confirmPasswordReset: async (uidb64, token, password, password2) => {
    try {
      const response = await api.post(
        `${config.AUTH_ENDPOINTS.PASSWORD_RESET_CONFIRM}${uidb64}/${token}/`, 
        { new_password: password }
      );
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la confirmation de la réinitialisation:', error.response?.data || error.message);
      throw error.response?.data || new Error('Une erreur est survenue.');
    }
  },
};

export default authService;
