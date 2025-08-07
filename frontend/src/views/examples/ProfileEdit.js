import React, { useState, useEffect } from "react";
import { 
  Card, CardBody, CardHeader, Row, Col, Alert, Button,
  Container, Form, FormGroup, Input, Label
} from "reactstrap";
import { useNavigate } from "react-router-dom";
import authService from "../../services/auth";
import clientService from "../../services/clientService";
import employeeService from "../../services/employeeService";

const ProfileEdit = () => {
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: ''
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  const currentUser = authService.getCurrentUser();

  useEffect(() => {
    const fetchProfile = async () => {
      const user = authService.getCurrentUser();
      if (!user) {
        setError("Veuillez vous connecter pour modifier votre profil");
        setLoading(false);
        return;
      }

      try {
        if (user.user_type === 'client' || user.role === 'client' || 
            user.role === 'Owner' || user.role === 'owner') {
          // Charger les données client
          const clientData = await clientService.getCurrent();
          setFormData({
            first_name: clientData.first_name || '',
            last_name: clientData.last_name || '',
            email: clientData.email || clientData.user?.email || ''
          });
        } else if (user.user_type === 'employee' || 
                  user.role === 'employee' || 
                  user.role === 'admin' || 
                  user.role === 'gestionnaire') {
          // Charger les données employé
          const employeeData = await employeeService.getCurrent();
          setFormData({
            first_name: employeeData.first_name || employeeData.user?.first_name || '',
            last_name: employeeData.last_name || employeeData.user?.last_name || '',
            email: employeeData.email || employeeData.user?.email || ''
          });
        } else {
          // Utilisateur standard (fallback)
          setFormData({
            first_name: user.first_name || '',
            last_name: user.last_name || '',
            email: user.email || ''
          });
        }
      } catch (err) {
        console.error("Erreur lors du chargement du profil:", err);
        setError("Erreur lors du chargement du profil");
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, []); // Pas de dépendances pour éviter la boucle infinie

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');

    try {
      console.log('FormData to update:', formData);
      console.log('Current user:', currentUser);
      
      if (currentUser.user_type === 'client' || currentUser.role === 'client' || 
          currentUser.role === 'Owner' || currentUser.role === 'owner') {
        // Mise à jour pour les clients
        const clientData = await clientService.getCurrent();
        console.log('Client data for update:', clientData);
        console.log('Updating client with ID:', clientData.id);
        
        const result = await clientService.update(clientData.id, formData);
        console.log('Update result:', result);
        
        setSuccess('Profil client mis à jour avec succès !');
        setTimeout(() => {
          navigate('/client/profile');
        }, 1500);
        
      } else if (currentUser.user_type === 'employee' || 
                currentUser.role === 'employee' || 
                currentUser.role === 'admin' || 
                currentUser.role === 'gestionnaire') {
        // Mise à jour pour les employés
        const employeeData = await employeeService.getCurrent();
        console.log('Employee data for update:', employeeData);
        console.log('Updating employee with ID:', employeeData.id);
        
        const result = await employeeService.update(employeeData.id, formData);
        console.log('Update result:', result);
        
        // Mettre à jour les données utilisateur dans le stockage local
        const updatedUser = {
          ...currentUser,
          first_name: formData.first_name,
          last_name: formData.last_name,
          email: formData.email
        };
        localStorage.setItem('user', JSON.stringify(updatedUser));
        
        setSuccess('Profil employé mis à jour avec succès !');
        setTimeout(() => {
          navigate('/admin/profile');
        }, 1500);
      } else {
        throw new Error("Type d'utilisateur non pris en charge");
      }
    } catch (err) {
      console.error("Erreur lors de la mise à jour:", err);
      setError(err.response?.data?.message || "Erreur lors de la mise à jour du profil");
    } finally {
      setSaving(false);
    }
  };

  if (!currentUser) {
    return (
      <div className="text-center mt-5">
        <Alert color="warning">Veuillez vous connecter pour modifier votre profil</Alert>
        <Button color="primary" className="mt-3" onClick={() => navigate('/auth/login')}>
          Se connecter
        </Button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="text-center mt-5">
        <div className="spinner-border text-primary" role="status">
          <span className="sr-only">Chargement...</span>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="header bg-gradient-info pb-8 pt-5 pt-md-8">
        <Container fluid>
          <Row className="align-items-center">
            <Col lg="6">
              <h1 className="text-white">Modifier mon profil</h1>
              <p className="text-white-50">
                Mettez à jour vos informations personnelles
              </p>
            </Col>
            <Col className="text-right" lg="6">
              <Button color="default" onClick={() => navigate('/client/profile')}>
                <i className="ni ni-bold-left mr-2" /> Retour au profil
              </Button>
            </Col>
          </Row>
        </Container>
      </div>

      <Container className="mt--7" fluid>
        <Row className="justify-content-center">
          <Col xl="8">
            <Card className="bg-secondary shadow">
              <CardHeader className="bg-white border-0">
                <h3 className="mb-0">Modifier les informations</h3>
              </CardHeader>
              <CardBody>
                {error && <Alert color="danger">{error}</Alert>}
                {success && <Alert color="success">{success}</Alert>}
                
                <Form onSubmit={handleSubmit}>
                  <div className="pl-lg-4">
                    <Row>
                      <Col lg="6">
                        <FormGroup>
                          <Label className="form-control-label" for="first_name">
                            Prénom
                          </Label>
                          <Input
                            className="form-control-alternative"
                            id="first_name"
                            name="first_name"
                            placeholder="Votre prénom"
                            type="text"
                            value={formData.first_name}
                            onChange={handleInputChange}
                            required
                          />
                        </FormGroup>
                      </Col>
                      <Col lg="6">
                        <FormGroup>
                          <Label className="form-control-label" for="last_name">
                            Nom
                          </Label>
                          <Input
                            className="form-control-alternative"
                            id="last_name"
                            name="last_name"
                            placeholder="Votre nom"
                            type="text"
                            value={formData.last_name}
                            onChange={handleInputChange}
                            required
                          />
                        </FormGroup>
                      </Col>
                    </Row>

                    <Row>
                      <Col lg="6">
                        <FormGroup>
                          <Label className="form-control-label" for="email">
                            Email
                          </Label>
                          <Input
                            className="form-control-alternative"
                            id="email"
                            name="email"
                            placeholder="votre@email.com"
                            type="email"
                            value={formData.email}
                            onChange={handleInputChange}
                            required
                          />
                        </FormGroup>
                      </Col>
                    </Row>

                    <Row>
                      <Col className="text-center">
                        <Button
                          color="primary"
                          type="submit"
                          disabled={saving}
                        >
                          {saving ? (
                            <>
                              <span className="spinner-border spinner-border-sm mr-2" role="status" aria-hidden="true"></span>
                              Enregistrement...
                            </>
                          ) : (
                            <>
                              <i className="ni ni-check-bold mr-2" />
                              Enregistrer les modifications
                            </>
                          )}
                        </Button>
                        <Button
                          color="secondary"
                          type="button"
                          className="ml-3"
                          onClick={() => navigate('/client/profile')}
                          disabled={saving}
                        >
                          Annuler
                        </Button>
                      </Col>
                    </Row>
                  </div>
                </Form>
              </CardBody>
            </Card>
          </Col>
        </Row>
      </Container>
    </>
  );
};

export default ProfileEdit;
