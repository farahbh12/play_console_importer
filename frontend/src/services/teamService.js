import api from './api';
import axios from 'axios';

// Create a public API instance without auth interceptors
const publicApi = axios.create({
  baseURL: api.defaults.baseURL,
});

const teamService = {
  /**
   * Récupère la liste des membres de l'équipe du tenant actuel.
   */
  getTeamMembers: async () => {
    try {
      const response = await api.get('/api/team/members/');
      return response.data;
    } catch (error) {
      console.error('Error fetching team members:', error);
      throw error;
    }
  },

  /**
   * Invite un nouveau membre dans l'équipe.
   */
  inviteMember: async (email, firstName, lastName) => {
    try {
      const response = await api.post('/api/team/invite/', { email, first_name: firstName, last_name: lastName });
      return response.data;
    } catch (error) {
      console.error('Error inviting team member:', error);
      throw error;
    }
  },

  /**
   * Vérifie la validité d'un token d'invitation.
   * L'erreur (ex: 404 Not Found) est volontairement non interceptée ici
   * pour être gérée par le composant qui appelle cette fonction.
   */
  checkInvitation: async (token) => {
    // Use the public instance for this public endpoint
    const response = await publicApi.get(`/api/team/check-invitation/${token}/`);
    return response.data; // Retourne les données en cas de succès (HTTP 200)
  },

  /**
   * Active une invitation en définissant le mot de passe de l'utilisateur.
   */
  verifyInvitation: async (token, password) => {
    // Use the public instance for this public endpoint
    const response = await publicApi.post(`/api/team/verify-invitation/${token}/`, { password });
    return response.data;
  }
};

export default teamService;