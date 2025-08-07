import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  CardHeader,
  CardBody,
  FormGroup,
  Form,
  Input,
  Button,
  Container,
  Row,
  Col,
  Spinner
} from "reactstrap";
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import abonnementService from '../../services/abonnementService';

const SubscriptionPage = () => {
  const navigate = useNavigate();
  
  // États
  const [formData, setFormData] = useState({
    type_abonnement: '', 
    nom: '',
    prenom: '',
    email: ''
  });

  const [loading, setLoading] = useState(false);
  const [formErrors, setFormErrors] = useState({});

  // Constantes
  const ABONNEMENT_TYPES = {
    BASIC: 'BASIC',
    PRO: 'PRO',
    ENTERPRISE: 'ENTERPRISE'
  };

  const abonnementOptions = [
    { value: '', label: 'Sélectionnez un type d\'abonnement', disabled: true },
    { value: ABONNEMENT_TYPES.BASIC, label: 'BASIC' },
    { value: ABONNEMENT_TYPES.PRO, label: 'PRO' },
    { value: ABONNEMENT_TYPES.ENTERPRISE, label: 'ENTERPRISE' }
  ];

  // Gestion des changements de formulaire
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    if (formErrors[name]) {
      setFormErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  // Validation du formulaire
  const validateForm = () => {
    const errors = {};
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!formData.nom.trim()) errors.nom = 'Le nom est requis';
    if (!formData.prenom.trim()) errors.prenom = 'Le prénom est requis';
    
    if (!formData.email) {
      errors.email = "L'email est requis";
    } else if (!emailRegex.test(formData.email)) {
      errors.email = "Veuillez entrer un email valide";
    }
    
    if (!Object.values(ABONNEMENT_TYPES).includes(formData.type_abonnement)) {
      errors.type_abonnement = 'Veuillez sélectionner un type d\'abonnement valide';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Soumission du formulaire
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      const subscriptionData = {
        email: formData.email,
        nom: formData.nom,
        prenom: formData.prenom,
        type_abonnement: formData.type_abonnement
      };

      const response = await abonnementService.souscrireAbonnement(subscriptionData);

      if (response.success) {
        toast.success(`Abonnement ${response.abonnement_type} créé avec succès pour ${response.prenom} ${response.nom}. Redirection en cours...`);
        
        // Réinitialisation du formulaire
        setFormData({
          type_abonnement: '',
          nom: '',
          prenom: '',
          email: ''
        });

        // Redirection après 2 secondes
        setTimeout(() => {
          navigate('/admin/gcs/validate');
        }, 2000);
      } else {
        throw new Error(response.error || 'Une erreur est survenue');
      }
    } catch (error) {
      console.error('Erreur:', error);
      toast.error(error.message || 'Une erreur est survenue lors de la souscription');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="header bg-gradient-info pb-8 pt-5 pt-md-8">
        <Container fluid>
          <div className="header-body">
            <h2 className="text-white">Souscription à un abonnement</h2>
            <p className="text-white-50">
              Remplissez le formulaire pour vous abonner à nos services
            </p>
          </div>
        </Container>
      </div>

      <Container className="mt--8 pb-5">
        <Row className="justify-content-center">
          <Col lg="8" md="10">
            <Card className="bg-secondary shadow">
              <CardHeader className="bg-white border-0">
                <h3 className="mb-0">Formulaire d'abonnement</h3>
              </CardHeader>
              <CardBody>
                <Form role="form" onSubmit={handleSubmit}>
                  <Row>
                    <Col md="6">
                      <FormGroup className={formErrors.prenom ? "has-danger" : "mb-3"}>
                        <label className="form-control-label" htmlFor="prenom">
                          Prénom <span className="text-danger">*</span>
                        </label>
                        <Input
                          className={`form-control-alternative ${formErrors.prenom ? 'is-invalid' : ''}`}
                          id="prenom"
                          name="prenom"
                          placeholder="Votre prénom"
                          type="text"
                          value={formData.prenom}
                          onChange={handleChange}
                          disabled={loading}
                        />
                        {formErrors.prenom && (
                          <div className="invalid-feedback d-block">{formErrors.prenom}</div>
                        )}
                      </FormGroup>
                    </Col>
                    <Col md="6">
                      <FormGroup className={formErrors.nom ? "has-danger" : "mb-3"}>
                        <label className="form-control-label" htmlFor="nom">
                          Nom <span className="text-danger">*</span>
                        </label>
                        <Input
                          className={`form-control-alternative ${formErrors.nom ? 'is-invalid' : ''}`}
                          id="nom"
                          name="nom"
                          placeholder="Votre nom"
                          type="text"
                          value={formData.nom}
                          onChange={handleChange}
                          disabled={loading}
                        />
                        {formErrors.nom && (
                          <div className="invalid-feedback d-block">{formErrors.nom}</div>
                        )}
                      </FormGroup>
                    </Col>
                  </Row>

                  <FormGroup className={formErrors.email ? "has-danger" : "mb-4"}>
                    <label className="form-control-label" htmlFor="email">
                      Email <span className="text-danger">*</span>
                    </label>
                    <Input
                      className={`form-control-alternative ${formErrors.email ? 'is-invalid' : ''}`}
                      id="email"
                      name="email"
                      placeholder="votre@email.com"
                      type="email"
                      value={formData.email}
                      onChange={handleChange}
                      disabled={loading}
                    />
                    {formErrors.email && (
                      <div className="invalid-feedback d-block">{formErrors.email}</div>
                    )}
                  </FormGroup>

                  <FormGroup className={formErrors.type_abonnement ? "has-danger" : "mb-4"}>
                    <label className="form-control-label" htmlFor="type_abonnement">
                      Type d'abonnement <span className="text-danger">*</span>
                    </label>
                    <Input
                      type="select"
                      className={`form-control-alternative ${formErrors.type_abonnement ? 'is-invalid' : ''}`}
                      id="type_abonnement"
                      name="type_abonnement"
                      value={formData.type_abonnement}
                      onChange={handleChange}
                      disabled={loading}
                    >
                      {abonnementOptions.map((option, index) => (
                        <option 
                          key={option.value || 'default'} 
                          value={option.value}
                          disabled={option.disabled || false}
                        >
                          {option.label}
                        </option>
                      ))}
                    </Input>
                    {formErrors.type_abonnement && (
                      <div className="invalid-feedback d-block">
                        {formErrors.type_abonnement}
                      </div>
                    )}
                  </FormGroup>

                  <div className="text-center">
                    <Button 
                      className="my-4" 
                      color="primary" 
                      type="submit" 
                      disabled={loading}
                      size="lg"
                    >
                      {loading ? (
                        <>
                          <Spinner size="sm" className="mr-2" />
                          Traitement en cours...
                        </>
                      ) : (
                        "Souscrire maintenant"
                      )}
                    </Button>
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

export default SubscriptionPage;