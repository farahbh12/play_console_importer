import React, { useEffect, useState } from 'react';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import {
  Card, CardHeader, Table, Container,
  Row, Col, CardBody, Spinner,
  Alert, Button, ButtonGroup, Badge
} from 'reactstrap';
import clientService from '../../services/clientService';

const ClientList = () => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [updating, setUpdating] = useState({});

  const fetchClients = async () => {
    try {
      setLoading(true);
      const clientsData = await clientService.getAll();
      console.log('Données reçues:', clientsData);

      if (!Array.isArray(clientsData)) {
        console.error('Les données reçues ne sont pas un tableau:', clientsData);
        throw new Error('Format de données incorrect reçu du serveur.');
      }

      const formattedClients = clientsData.map((client, index) => ({
        id: client.id,
        user_id: client.user_id,
        first_name: client.first_name,
        last_name: client.last_name,
        email: client.email,
        role: client.role,
        type_abonnement: client.abonnement_type,
        is_active: client.is_active
      }));
      // Ne garder que les comptes Owner (exclure les membres invités)
      const ownersOnly = formattedClients.filter(c => {
        const role = (c.role || '').toString().trim().toUpperCase();
        return role === 'OWNER';
      });
      setClients(ownersOnly);
      setError(null);
    } catch (err) {
      console.error('Erreur chargement clients:', err);
      const errorMessage = err.response?.data?.error || "Erreur lors du chargement des clients.";
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (userId, activate) => {
    if (!userId) {
      console.error('Erreur: ID utilisateur manquant');
      toast.error('Erreur: ID utilisateur manquant');
      return;
    }

    try {
      setUpdating(prev => ({ ...prev, [userId]: true }));

      // Mise à jour optimiste
      setClients(prevClients =>
        prevClients.map(client =>
          client.user_id === userId ? { ...client, is_active: activate } : client
        )
      );

      // Appel API avec la nouvelle méthode
      await clientService.setStatus(userId, activate);
      toast.success(`Client ${activate ? 'activé' : 'désactivé'} avec succès`);

    } catch (error) {
      console.error('Erreur lors de la mise à jour du statut:', error);
      toast.error(error.response?.data?.detail || 'Erreur lors de la mise à jour du statut');
      
      // Rollback en cas d'erreur
      setClients(prevClients =>
        prevClients.map(client =>
          client.user_id === userId ? { ...client, is_active: !activate } : client
        )
      );
    } finally {
      setUpdating(prev => ({ ...prev, [userId]: false }));
    }
  };

  useEffect(() => {
    fetchClients();
  }, []);

  if (loading) {
    return (
      <div className="text-center my-5">
        <Spinner color="primary" />
        <p className="mt-2">Chargement des clients...</p>
      </div>
    );
  }

  return (
    <>
      <div className="header bg-gradient-info pb-8 pt-5 pt-md-8">
        <Container fluid>
          <div className="header-body" />
        </Container>
      </div>

      <Container className="mt--7" fluid>
        <Row>
          <div className="col">
            <Card className="shadow">
              <CardHeader className="border-0">
                <Row className="align-items-center">
                  <Col xs="8">
                    <h3 className="mb-0">Liste des clients</h3>
                  </Col>
                </Row>
              </CardHeader>

              {error ? (
                <Alert color="danger" className="m-3">
                  {error}
                  <Button color="link" onClick={fetchClients} className="p-0 ml-2">
                    Réessayer
                  </Button>
                </Alert>
              ) : clients.length === 0 ? (
                <Alert color="info" className="m-3">
                  Aucun client trouvé.
                </Alert>
              ) : (
                <div className="table-responsive">
                  <Table className="align-items-center table-flush" hover>
                    <thead className="thead-light">
                      <tr>
                        <th>Prénom</th>
                        <th>Nom</th>
                        <th>Email</th>
                        <th>Rôle</th>
                        <th>Type Abonnement</th>
                        <th>Statut</th>
                        <th className="text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {clients.map((client) => {
                        const isActive = client.is_active;
                        const isUpdating = updating[client.user_id];

                        return (
                          <tr key={client.id}>
                            <td>{client.first_name || '—'}</td>
                            <td>{client.last_name || '—'}</td>
                            <td>{client.email || '—'}</td>
                            <td>{client.role || '—'}</td>
                            <td>{client.type_abonnement || '—'}</td>
                            <td>
                              <Badge color={isActive ? 'success' : 'danger'}>
                                {isActive ? 'Actif' : 'Inactif'}
                              </Badge>
                            </td>
                            <td className="text-right">
                              <ButtonGroup size="sm">
                                <Button
                                  color="success"
                                  onClick={() => handleStatusUpdate(client.user_id, true)}
                                  disabled={isUpdating || isActive}
                                  className="mr-1"
                                >
                                  {isUpdating ? <Spinner size="sm" /> : 'Activer'}
                                </Button>
                                <Button
                                  color="danger"
                                  onClick={() => handleStatusUpdate(client.user_id, false)}
                                  disabled={isUpdating || !isActive}
                                >
                                  {isUpdating ? <Spinner size="sm" /> : 'Désactiver'}
                                </Button>
                              </ButtonGroup>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </Table>
                </div>
              )}

              <CardBody className="py-4">
                {/* Espace pour la pagination */}
              </CardBody>
            </Card>
          </div>
        </Row>
      </Container>
    </>
  );
};

export default ClientList;