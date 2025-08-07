import React, { useState, useEffect } from 'react';
import {
  Card, CardHeader, Table, Container, Row, Col,
  Button, Badge, Spinner, Alert, Modal,
  ModalHeader, ModalBody, ModalFooter, Form, FormGroup, Label, Input
} from 'reactstrap';
import { toast } from 'react-toastify';
import abonnementService from '../../services/abonnementService';

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
        await abonnementService.update(currentAbonnement.id_abonnement, formData);
        toast.success('Abonnement mis à jour avec succès');
        fetchAbonnements();
        toggleModal();
      }
    } catch (error) {
      console.error('Erreur:', error);
      toast.error(error.response?.data?.message || 'Une erreur est survenue');
    }
  };

  const handleToggleStatus = async (abonnement) => {
    if (window.confirm(`Êtes-vous sûr de vouloir ${abonnement.is_active ? 'désactiver' : 'activer'} cet abonnement ?`)) {
      try {
        await abonnementService.toggle(abonnement.id_abonnement);
        toast.success(`Abonnement ${abonnement.is_active ? 'désactivé' : 'activé'} avec succès`);
        fetchAbonnements();
      } catch (error) {
        console.error('Erreur:', error);
        toast.error(error.response?.data?.message || 'Erreur lors de la modification du statut');
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
                    <th scope="col">Client</th>
                    <th scope="col">Email</th>
                    <th scope="col">Statut</th>
                    <th scope="col">Date de création</th>
                    <th scope="col" className="text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {abonnements.length > 0 ? (
                    abonnements.map((abonnement) => (
                      <tr key={abonnement.id_abonnement}>
                        <td>
                          {abonnement.type_abonnement === 'BASIC' && 'BASIC'}
                          {abonnement.type_abonnement === 'PRO' && 'Professionnel'}
                          {abonnement.type_abonnement === 'ENTERPRISE' && 'ENTERPRISE'}
                        </td>
                        <td>{abonnement.prenom} {abonnement.nom}</td>
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
                      <td colSpan="6" className="text-center">
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
                required
              >
                <option value="BASIC">Basique</option>
                <option value="PRO">Professionnel</option>
                <option value="ENTERPRISE">Entreprise</option>
              </Input>
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