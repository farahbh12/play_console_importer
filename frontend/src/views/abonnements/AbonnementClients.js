import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Box,
  Typography,
  CircularProgress,
  Alert,
  Snackbar,
  Chip,
  Avatar,
  Divider
} from '@mui/material';
import { 
  ArrowBack as ArrowBackIcon, 
  PersonAdd as PersonAddIcon, 
  PersonRemove as PersonRemoveIcon,
  Check as CheckIcon,
  Close as CloseIcon
} from '@mui/icons-material';
import abonnementService from '../../services/abonnementService';
import userService from '../../services/userService';

const AbonnementClients = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [abonnement, setAbonnement] = useState(null);
  const [clients, setClients] = useState([]);
  const [availableClients, setAvailableClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [openAddDialog, setOpenAddDialog] = useState(false);
  const [selectedClient, setSelectedClient] = useState('');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  // Charger les données de l'abonnement et des clients
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Récupérer les détails de l'abonnement
        const abonnementResponse = await abonnementService.getById(id);
        setAbonnement(abonnementResponse.data);
        
        // Récupérer les clients de l'abonnement
        const clientsResponse = await abonnementService.getClients(id);
        setClients(clientsResponse.data);
        
        setError(null);
      } catch (err) {
        setError('Erreur lors du chargement des données');
        console.error('Erreur:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  // Charger les clients disponibles pour l'ajout
  const loadAvailableClients = async () => {
    try {
      const response = await userService.getAll();
      // Filtrer pour ne garder que les clients qui ne sont pas déjà dans l'abonnement
      const currentClientIds = new Set(clients.map(c => c.id));
      const available = response.data.filter(user => !currentClientIds.has(user.id));
      setAvailableClients(available);
    } catch (err) {
      console.error('Erreur lors du chargement des clients disponibles:', err);
    }
  };

  // Gérer l'ouverture du dialogue d'ajout
  const handleOpenAddDialog = async () => {
    await loadAvailableClients();
    setSelectedClient('');
    setOpenAddDialog(true);
  };

  // Gérer la fermeture du dialogue
  const handleCloseAddDialog = () => {
    setOpenAddDialog(false);
  };

  // Ajouter un client à l'abonnement
  const handleAddClient = async () => {
    if (!selectedClient) return;
    
    try {
      await abonnementService.addClient(id, selectedClient);
      
      // Mettre à jour la liste des clients
      const response = await abonnementService.getClients(id);
      setClients(response.data);
      
      // Mettre à jour la liste des clients disponibles
      await loadAvailableClients();
      
      setSnackbar({ 
        open: true, 
        message: 'Client ajouté avec succès', 
        severity: 'success' 
      });
      
      setOpenAddDialog(false);
    } catch (err) {
      setSnackbar({ 
        open: true, 
        message: `Erreur: ${err.response?.data?.error || 'Une erreur est survenue'}`,
        severity: 'error' 
      });
    }
  };

  // Retirer un client de l'abonnement
  const handleRemoveClient = async (clientId) => {
    if (window.confirm('Êtes-vous sûr de vouloir retirer ce client de l\'abonnement ?')) {
      try {
        await abonnementService.removeClient(id, clientId);
        
        // Mettre à jour la liste des clients
        const response = await abonnementService.getClients(id);
        setClients(response.data);
        
        // Recharger les clients disponibles
        await loadAvailableClients();
        
        setSnackbar({ 
          open: true, 
          message: 'Client retiré avec succès', 
          severity: 'success' 
        });
      } catch (err) {
        setSnackbar({ 
          open: true, 
          message: `Erreur: ${err.response?.data?.error || 'Une erreur est survenue'}`,
          severity: 'error' 
        });
      }
    }
  };

  // Gérer la fermeture de la notification
  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  // Afficher l'avatar de l'utilisateur
  const renderAvatar = (user) => {
    if (user.avatar) {
      return <Avatar alt={user.username} src={user.avatar} />;
    }
    return (
      <Avatar>
        {user.first_name?.[0] || user.username?.[0] || 'U'}
      </Avatar>
    );
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ my: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <>
      <Button
        startIcon={<ArrowBackIcon />}
        onClick={() => navigate('/abonnements')}
        sx={{ mb: 2 }}
      >
        Retour à la liste des abonnements
      </Button>

      <Card>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
            <Typography variant="h5" component="h2">
              Gestion des clients - {abonnement?.type_abonnement_display || 'Abonnement'}
            </Typography>
            <Button
              variant="contained"
              color="primary"
              startIcon={<PersonAddIcon />}
              onClick={handleOpenAddDialog}
              disabled={availableClients.length === 0}
            >
              Ajouter un client
            </Button>
          </Box>


          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Utilisateur</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Date d'ajout</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {clients.length > 0 ? (
                  clients.map((client) => (
                    <TableRow key={client.id}>
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={1}>
                          {renderAvatar(client)}
                          <span>
                            {client.first_name} {client.last_name || ''}
                          </span>
                        </Box>
                      </TableCell>
                      <TableCell>{client.email}</TableCell>
                      <TableCell>
                        {new Date(client.date_joined).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <IconButton 
                          color="error"
                          onClick={() => handleRemoveClient(client.id)}
                          title="Retirer du client"
                        >
                          <PersonRemoveIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={4} align="center">
                      Aucun client trouvé pour cet abonnement
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Dialogue d'ajout de client */}
      <Dialog open={openAddDialog} onClose={handleCloseAddDialog} maxWidth="sm" fullWidth>
        <DialogTitle>Ajouter un client à l'abonnement</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <TextField
              select
              fullWidth
              label="Sélectionner un client"
              value={selectedClient}
              onChange={(e) => setSelectedClient(e.target.value)}
              variant="outlined"
              margin="normal"
            >
              {availableClients.map((client) => (
                <MenuItem key={client.id} value={client.id}>
                  {client.first_name} {client.last_name} ({client.email})
                </MenuItem>
              ))}
            </TextField>
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={handleCloseAddDialog} color="inherit">
            Annuler
          </Button>
          <Button 
            onClick={handleAddClient} 
            variant="contained" 
            color="primary"
            disabled={!selectedClient}
            startIcon={<CheckIcon />}
          >
            Ajouter
          </Button>
        </DialogActions>
      </Dialog>

      {/* Notification */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </>
  );
};

export default AbonnementClients;