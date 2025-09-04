import React, { useState, useEffect } from 'react';
import {
  Card, CardHeader, Table, Container, Row, Col,
  Button, Badge, Spinner, Alert, Modal,
  ModalHeader, ModalBody, ModalFooter, Form, FormGroup, Label, Input
} from 'reactstrap';
import { toast } from 'react-toastify';
import abonnementService from '../../services/abonnementService';
import clientService from '../../services/clientService';
import api from '../../services/api'; // Même chemin que dans Register.js et Assistant.js

const AbonnementList = () => {
  const [abonnements, setAbonnements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [modal, setModal] = useState(false);
  const [currentAbonnement, setCurrentAbonnement] = useState(null);
  const [formData, setFormData] = useState({
    type_abonnement: 'BASIC',
    is_active: true
  });

  const fetchAbonnements = async () => {
    try {
      setLoading(true);
      const data = await abonnementService.getAll();
      setAbonnements(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Erreur détaillée:', err);
      setError('Erreur lors du chargement des abonnements');
      toast.error('Erreur lors du chargement des abonnements');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAbonnements();
  }, []);

  const toggleModal = () => setModal(!modal);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleOpenEdit = (abonnement) => {
    setCurrentAbonnement(abonnement);
    setFormData({
      type_abonnement: abonnement.type_abonnement,
      is_active: abonnement.is_active
    });
    toggleModal();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (currentAbonnement) {
        // 1) Changer l'abonnement du client si le type a changé (évite le conflit d'unicité)
        if (formData.type_abonnement !== currentAbonnement.type_abonnement) {
          if (!currentAbonnement.user_id) {
            throw new Error("Impossible d'identifier le client (user_id manquant)");
          }
          await clientService.changeAbonnement(currentAbonnement.user_id, formData.type_abonnement);
          toast.success("Type d'abonnement du client mis à jour");
        }

        // 2) Mettre à jour uniquement le statut is_active si changé
        if (formData.is_active !== currentAbonnement.is_active) {
          await abonnementService.update(currentAbonnement.id, { is_active: formData.is_active });
          toast.success('Statut de l\'abonnement mis à jour');
        }
        fetchAbonnements();
        toggleModal();
      }
    } catch (error) {
      console.error('Erreur:', error);
      const apiMsg = error.response?.data?.error || error.response?.data?.message;
      toast.error(apiMsg || error.message || 'Une erreur est survenue');
    }
  };

  const handleToggleStatus = async (abonnement) => {
    console.log('Abonnement reçu dans handleToggleStatus:', abonnement);
    
    if (!abonnement.id || !abonnement.client_id) {
      console.error('ID d\'abonnement ou ID client manquant dans l\'objet:', abonnement);
      toast.error('Informations manquantes pour effectuer cette action');
      return;
    }

    if (window.confirm(`Êtes-vous sûr de vouloir ${abonnement.is_active ? 'désactiver' : 'activer'} l'abonnement de ce client ?`)) {
      try {
        console.log('Appel de toggle avec ID client:', abonnement.client_id, 'et ID abonnement:', abonnement.id);
        
        // Appel à l'API pour mettre à jour le statut de l'abonnement
        const response = await api.patch(`/abonnements/${abonnement.id}/toggle-active/`, null, {
          params: {
            action: abonnement.is_active ? 'deactivate' : 'activate'
          }
        });
        
        console.log('Réponse du serveur:', response.data);
        
        // Mettre à jour l'état local
        setAbonnements(prevAbonnements => 
          prevAbonnements.map(item => 
            item.id === abonnement.id && item.client_id === abonnement.client_id
              ? { ...item, is_active: !abonnement.is_active }
              : item
          )
        );
        
        toast.success(`Abonnement ${abonnement.is_active ? 'désactivé' : 'activé'} avec succès pour ce client`);
      } catch (error) {
        console.error('Erreur lors du changement de statut de l\'abonnement:', error);
        const errorMessage = error.response?.data?.error || 'Erreur lors de la modification du statut';
        toast.error(errorMessage);
      }
    }
  };

  if (loading) {
    return (
      <div className="text-center my-5">
        <Spinner color="primary" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert color="danger" className="m-3">
        {error}
      </Alert>
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
                    <h3 className="mb-0">Liste des abonnements</h3>
                  </Col>
                </Row>
              </CardHeader>
              <Table className="align-items-center table-flush" responsive>
                <thead className="thead-light">
                  <tr>
                    <th scope="col">Type d'abonnement</th>
                    <th scope="col">Email</th>
                    <th scope="col">Statut</th>
                    <th scope="col">Date de création</th>
                    <th scope="col" className="text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {abonnements.length > 0 ? (
                    abonnements.map((abonnement) => (
                      <tr key={abonnement.id}>
                        <td>
                          {abonnement.type_abonnement === 'BASIC' && 'BASIC'}
                          {abonnement.type_abonnement === 'PRO' && 'Professionnel'}
                          {abonnement.type_abonnement === 'ENTERPRISE' && 'ENTERPRISE'}
                        </td>
                        <td>{abonnement.email || '-'}</td>
                        <td>
                          <Badge color={abonnement.is_active ? 'success' : 'danger'}>
                            {abonnement.is_active ? 'Actif' : 'Inactif'}
                          </Badge>
                        </td>
                        <td>{new Date(abonnement.date_creation).toLocaleDateString()}</td>
                        <td className="text-right">
                          <Button
                            color="primary"
                            size="sm"
                            className="mr-2"
                            onClick={() => handleOpenEdit(abonnement)}
                          >
                            <i className="fas fa-edit" /> Modifier
                          </Button>
                          <Button
                            color={abonnement.is_active ? 'danger' : 'success'}
                            size="sm"
                            onClick={() => handleToggleStatus(abonnement)}
                          >
                            {abonnement.is_active ? 'Désactiver' : 'Activer'}
                          </Button>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="5" className="text-center">
                        Aucun abonnement trouvé
                      </td>
                    </tr>
                  )}
                </tbody>
              </Table>
            </Card>
          </div>
        </Row>
      </Container>

      {/* Modal de modification */}
      <Modal isOpen={modal} toggle={toggleModal}>
        <ModalHeader toggle={toggleModal}>
          {currentAbonnement ? 'Modifier l\'abonnement' : 'Nouvel abonnement'}
        </ModalHeader>
        <Form onSubmit={handleSubmit}>
          <ModalBody>
            <FormGroup>
              <Label>Type d'abonnement</Label>
              <Input
                type="select"
                name="type_abonnement"
                value={formData.type_abonnement}
                onChange={handleInputChange}
                // Autoriser la modification du type d'abonnement par l'admin/manager
              >
                <option value="BASIC">Basique</option>
                <option value="PRO">Professionnel</option>
                <option value="ENTERPRISE">Entreprise</option>
              </Input>
              <small className="text-muted">Modifiez le type d'abonnement après la demande du client.</small>
            </FormGroup>
            <FormGroup check className="mt-3">
              <Label check>
                <Input
                  type="checkbox"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleInputChange}
                />{' '}
                Actif
              </Label>
            </FormGroup>
          </ModalBody>
          <ModalFooter>
            <Button color="secondary" onClick={toggleModal}>
              Annuler
            </Button>
            <Button color="primary" type="submit">
              Enregistrer
            </Button>
          </ModalFooter>
        </Form>
      </Modal>
    </>
  );
};

export default AbonnementList;