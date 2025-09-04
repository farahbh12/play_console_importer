import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import classnames from 'classnames';
import api from '../../services/api';
import SubscriptionSelection from '../../components/Subscription/SubscriptionSelection';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUser, faEnvelope, faLock, faIdBadge } from '@fortawesome/free-solid-svg-icons';
import {
  Button,
  Card,
  CardBody,
  CardHeader,
  CardFooter,
  FormGroup,
  Form,
  Input,
  InputGroupText,
  InputGroup,
  Row,
  Col,
  Alert,
  Nav,
  NavItem,
  NavLink,
  FormFeedback,
  Container,
  Label
} from 'reactstrap';

const Register = () => {
  // État pour gérer l'étape actuelle (1: formulaire, 2: sélection d'abonnement)
  const [currentStep, setCurrentStep] = useState(1);
  
  // Données du formulaire d'inscription
  const [formData, setFormData] = useState({
    userType: 'client',
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: '',
    roleEmploye: 'Administrateur'
  });
  
  // Données de l'utilisateur créé (pour l'étape 2)
  const [createdUser, setCreatedUser] = useState(null);
  
  // États pour les messages et le chargement
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Gestion des erreurs de formulaire
  const [fieldErrors, setFieldErrors] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: '',
    roleEmploye: ''
  });
  
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Effacer l'erreur du champ lors de la modification
    if (fieldErrors[name]) {
      setFieldErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };
  
  const handleSubscriptionComplete = () => {
    setSuccessMsg("Inscription et activation réussies ! Redirection vers la page de connexion...");
    setTimeout(() => navigate('/auth/login'), 2000);
  };
  
  const goBackToForm = () => {
    setCurrentStep(1);
    setError('');
    setSuccessMsg('');
  };

  const validateForm = () => {
    const { firstName, lastName, email, password, confirmPassword } = formData;
    const errors = {
      firstName: !firstName ? 'Prénom requis.' : '',
      lastName: !lastName ? 'Nom requis.' : '',
      email: !email ? 'Email requis.' : '',
      password: !password ? 'Mot de passe requis.' : 
               password.length < 8 ? 'Minimum 8 caractères.' : '',
      confirmPassword: !confirmPassword ? 'Confirmation requise.' : 
                      password !== confirmPassword ? 'Les mots de passe ne correspondent pas.' : ''
    };
    
    const hasErrors = Object.values(errors).some(error => error !== '');
    setFieldErrors(errors);
    
    return !hasErrors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSuccessMsg('');
    setError('');

    if (!validateForm()) {
      setError('Veuillez corriger les erreurs dans le formulaire.');
      return;
    }

    const { firstName, lastName, email, password, confirmPassword, userType, roleEmploye } = formData;
    
    // Vérifier si on essaie de créer un administrateur alors qu'il en existe déjà un
    if (userType === 'employee' && roleEmploye === 'Administrateur') {
      try {
        // Vérifier si un administrateur existe déjà
        const response = await api.get('/employee/check-admin/');
        if (response.data.admin_exists) {
          setError("Un compte administrateur existe déjà. Vous ne pouvez pas en créer un autre.");
          return;
        }
      } catch (error) {
        console.error('Erreur lors de la vérification de l\'administrateur existant:', error);
        setError('Erreur lors de la vérification des droits administrateur.');
        return;
      }
    }

    setIsSubmitting(true);

    try {
      const data = {
        first_name: firstName,
        last_name: lastName,
        email,
        password,
        password_confirm: confirmPassword,
      };

      if (userType === 'employee') {
        data.role_employe = roleEmploye;
      }
      
      const response = await api.post(`/${userType}/register/`, data);
      
      if (userType === 'client') {
        setCreatedUser({
          id: response.data.client_id,
          email: response.data.email,
          first_name: firstName,
          last_name: lastName
        });
        setCurrentStep(2);
        setSuccessMsg("Inscription réussie ! Veuillez choisir un abonnement pour continuer.");
      } else {
        setSuccessMsg("Inscription réussie ! Redirection vers la page de connexion...");
        setTimeout(() => navigate('/auth/login'), 2000);
      }
    } catch (error) {
      console.error('Registration error:', error);
      
      if (error.response?.data?.email) {
        setError('Cet email est déjà utilisé.');
      } else if (error.response?.data?.errors) {
        const errorMessages = Object.values(error.response.data.errors).flat();
        setError(errorMessages.join(' '));
      } else {
        setError('Une erreur est survenue lors de l\'inscription. Veuillez réessayer.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Étape 1 : Formulaire d'inscription
  const renderStep1 = () => (
    <div className="container mt-5">
      <Row className="justify-content-center">
        <Col lg="8" xl="7">
          <Card className="bg-secondary shadow border-0 p-4">
            <CardHeader className="bg-transparent pb-4">
              <div className="text-center">
                <h2 className="text-dark">Créer un compte</h2>
                <p className="text-muted">Choisissez votre type d'utilisateur</p>
              </div>
              <Nav className="nav-fill mt-3" pills>
                <NavItem>
                  <NavLink
                    className={classnames({ active: formData.userType === 'client' })}
                    href="#pablo"
                    onClick={e => {
                      e.preventDefault();
                      setFormData(prev => ({ ...prev, userType: 'client' }));
                    }}
                  >
                    Client
                  </NavLink>
                </NavItem>
                <NavItem>
                  <NavLink
                    className={classnames({ active: formData.userType === 'employee' })}
                    href="#pablo"
                    onClick={e => {
                      e.preventDefault();
                      setFormData(prev => ({ ...prev, userType: 'employee' }));
                    }}
                  >
                    Employé
                  </NavLink>
                </NavItem>
              </Nav>
            </CardHeader>

            <CardBody className="px-lg-5 py-lg-4">
              {error && (
                <Alert color="danger" className="mb-4">
                  {error}
                </Alert>
              )}
              {successMsg && <Alert color="success">{successMsg}</Alert>}
              <Form role="form" onSubmit={handleSubmit}>
                <Row>
                  <Col md="6">
                    <FormGroup>
                      <InputGroup className="input-group-alternative mb-3">
                        <InputGroupText addonType="prepend">
                          <FontAwesomeIcon icon={faUser} />
                        </InputGroupText>
                        <Input
                          placeholder="Prénom"
                          type="text"
                          name="firstName"
                          value={formData.firstName}
                          onChange={handleChange}
                          required
                          invalid={!!fieldErrors.firstName}
                        />
                        {fieldErrors.firstName && <FormFeedback>{fieldErrors.firstName}</FormFeedback>}
                      </InputGroup>
                    </FormGroup>
                  </Col>
                  <Col md="6">
                    <FormGroup>
                      <InputGroup className="input-group-alternative mb-3">
                        <Input
                          placeholder="Nom"
                          type="text"
                          name="lastName"
                          value={formData.lastName}
                          onChange={handleChange}
                          required
                          invalid={!!fieldErrors.lastName}
                        />
                        {fieldErrors.lastName && <FormFeedback>{fieldErrors.lastName}</FormFeedback>}
                      </InputGroup>
                    </FormGroup>
                  </Col>
                </Row>

                <FormGroup>
                  <InputGroup className="input-group-alternative mb-3">
                    <InputGroupText addonType="prepend">
                      <FontAwesomeIcon icon={faEnvelope} />
                    </InputGroupText>
                    <Input
                      placeholder="Email"
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      required
                      invalid={!!fieldErrors.email}
                    />
                    {fieldErrors.email && <FormFeedback>{fieldErrors.email}</FormFeedback>}
                  </InputGroup>
                </FormGroup>

                <Row>
                  <Col md="6">
                    <FormGroup>
                      <InputGroup className="input-group-alternative">
                        <InputGroupText addonType="prepend">
                          <FontAwesomeIcon icon={faLock} />
                        </InputGroupText>
                        <Input
                          placeholder="Mot de passe"
                          type="password"
                          name="password"
                          value={formData.password}
                          onChange={handleChange}
                          required
                          invalid={!!fieldErrors.password}
                        />
                        {fieldErrors.password && <FormFeedback>{fieldErrors.password}</FormFeedback>}
                      </InputGroup>
                      <small className="text-muted">Minimum 8 caractères</small>
                    </FormGroup>
                  </Col>
                  <Col md="6">
                    <FormGroup>
                      <InputGroup className="input-group-alternative">
                        <Input
                          placeholder="Confirmer le mot de passe"
                          type="password"
                          name="confirmPassword"
                          value={formData.confirmPassword}
                          onChange={handleChange}
                          required
                          invalid={!!fieldErrors.confirmPassword}
                        />
                        {fieldErrors.confirmPassword && <FormFeedback>{fieldErrors.confirmPassword}</FormFeedback>}
                      </InputGroup>
                    </FormGroup>
                  </Col>
                </Row>

                {formData.userType === 'employee' && (
                  <FormGroup>
                    <InputGroup className="input-group-alternative mb-3">
                      <InputGroupText addonType="prepend">
                        <FontAwesomeIcon icon={faIdBadge} />
                      </InputGroupText>
                      <Input
                        type="select"
                        name="roleEmploye"
                        value={formData.roleEmploye}
                        onChange={handleChange}
                        invalid={!!fieldErrors.roleEmploye}
                      >
                        <option value="Administrateur">Administrateur</option>
                        <option value="Gestionnaire">Gestionnaire</option>
                      </Input>
                      {fieldErrors.roleEmploye && <FormFeedback>{fieldErrors.roleEmploye}</FormFeedback>}
                    </InputGroup>
                  </FormGroup>
                )}

                <div className="text-center">
                  <Button color="primary" type="submit" disabled={isSubmitting} block>
                    {isSubmitting ? 'Inscription en cours...' : "S'inscrire"}
                  </Button>
                </div>
              </Form>
            </CardBody>

            <CardFooter className="bg-transparent">
              <div className="text-center text-muted">
                <small>Vous avez déjà un compte ? </small>
                <Link to="/auth/login" className="text-primary font-weight-bold">
                  <small>Se connecter</small>
                </Link>
              </div>
            </CardFooter>
          </Card>
        </Col>
      </Row>
    </div>
  );

  // Étape 2 : Sélection de l'abonnement
  const renderStep2 = () => (
    <div className="container mt-5">
      <Row className="justify-content-center">
        <Col lg="8" xl="7">
          <Card className="bg-secondary shadow border-0 p-4">
            <CardHeader className="bg-transparent pb-4">
              <div className="d-flex justify-content-between align-items-center">
                <h2 className="text-dark mb-0">Choisissez votre abonnement</h2>
                <Button color="link" onClick={goBackToForm} className="text-primary">
                  <i className="fas fa-arrow-left me-2"></i> Retour
                </Button>
              </div>
            </CardHeader>
            <CardBody>
              {error && (
                <Alert color="danger" className="mb-4">
                  {error}
                </Alert>
              )}
              {successMsg && <Alert color="success">{successMsg}</Alert>}
              
              <p className="mb-4">
                Bonjour {createdUser?.first_name}, veuillez choisir un abonnement pour activer votre compte.
              </p>
              
              <SubscriptionSelection 
                userData={createdUser} 
                onComplete={handleSubscriptionComplete}
              />
              
              <div className="text-center mt-4">
                <p className="text-muted">
                  Vous pourrez changer d'abonnement à tout moment depuis votre espace client.
                </p>
              </div>
            </CardBody>
          </Card>
        </Col>
      </Row>
    </div>
  );

  return (
    <>
      {currentStep === 1 ? renderStep1() : renderStep2()}
    </>
  );
};

export default Register;