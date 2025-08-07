import React, { useState, useEffect } from "react";
import { 
  Card, CardBody, CardHeader, Row, Col, Alert, Button,
  Container, Form, FormGroup, Input, Label
} from "reactstrap";
import { useNavigate } from "react-router-dom";
import authService from "../../services/auth";
import employeeService from "../../services/employeeService";

const AdminProfileEdit = () => {
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

  useEffect(() => {
    const fetchProfile = async () => {
      setLoading(true);
      try {
        const employeeData = await employeeService.getCurrent();
        setFormData({
          first_name: employeeData.first_name || '',
          last_name: employeeData.last_name || '',
          email: employeeData.email || ''
        });
      } catch (err) {
        console.error("Erreur lors du chargement du profil employé:", err);
        setError("Impossible de charger les informations du profil. Veuillez réessayer.");
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');

    try {
      // Pas besoin de refaire un fetch, l'ID est dans l'objet retourné par getCurrent() initial
      // Mais pour être sûr, on le refait au cas où l'ID n'est pas stocké
      const currentEmployeeData = await employeeService.getCurrent();
      if (!currentEmployeeData.id) {
        throw new Error("L'identifiant de l'employé est introuvable.");
      }

      await employeeService.update(currentEmployeeData.id, formData);
      
      setSuccess('Profil mis à jour avec succès ! Redirection en cours...');
      setTimeout(() => {
        navigate('/admin/profile');
      }, 2000);

    } catch (err) {
      console.error("Erreur lors de la mise à jour du profil:", err);
      const errorMessage = err.response?.data ? JSON.stringify(err.response.data) : err.message;
      setError(`La mise à jour a échoué : ${errorMessage}`);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="text-center my-5">Chargement...</div>;
  }

  return (
    <>
      <div className="header bg-gradient-info pb-8 pt-5 pt-md-8">
        <Container fluid>
          <div className="header-body">
            {/* Card stats */}
          </div>
        </Container>
      </div>
      <Container className="mt--7" fluid>
        <Row>
          <Col className="order-xl-1" xl="12">
            <Card className="bg-secondary shadow">
              <CardHeader className="bg-white border-0">
                <Row className="align-items-center">
                  <Col xs="8">
                    <h3 className="mb-0">Modifier mon profil</h3>
                  </Col>
                </Row>
              </CardHeader>
              <CardBody>
                {error && <Alert color="danger">{error}</Alert>}
                {success && <Alert color="success">{success}</Alert>}
                
                <Form onSubmit={handleSubmit}>
                  <div className="pl-lg-4">
                    <Row>
                      <Col lg="6">
                        <FormGroup>
                          <Label className="form-control-label" htmlFor="first_name">Prénom</Label>
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
                          <Label className="form-control-label" htmlFor="last_name">Nom</Label>
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
                          <Label className="form-control-label" htmlFor="email">Email</Label>
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
                        <Button color="primary" type="submit" disabled={saving}>
                          {saving ? 'Enregistrement...' : 'Enregistrer les modifications'}
                        </Button>
                        <Button color="secondary" type="button" className="ml-3" onClick={() => navigate('/admin/profile')} disabled={saving}>
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

export default AdminProfileEdit;
