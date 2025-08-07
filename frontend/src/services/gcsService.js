import axios from 'axios';

const API_URL = 'http://localhost:8000'; // Remplacez par votre URL backend

const gcsService = {
  validateGcsUri: async (email, uri) => {
    const formData = new URLSearchParams();
    formData.append('email', email);
    formData.append('uri', uri);
    
    try {
      const response = await axios.post(`${API_URL}/validate-gcs-uri/`, formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        withCredentials: true // Important pour les sessions Django
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Erreur lors de la validation de l\'URI GCS' };
    }
  },

  getGcsFiles: async () => {
    try {
      const response = await axios.get(`${API_URL}/display-gcs-files/`, {
        withCredentials: true
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Erreur lors de la récupération des fichiers' };
    }
  }
};

export default gcsService;