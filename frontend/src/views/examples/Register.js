import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import classnames from 'classnames';
import api from '../../services/api';
import {
  Button,
  Card,
  CardBody,
  CardHeader,
  CardFooter,
  FormGroup,
  Form,
  Input,
  InputGroupAddon,
  InputGroupText,
  InputGroup,
  Row,
  Col,
  Alert,
  Nav,
  NavItem,
  NavLink
} from 'reactstrap';

const Register = () => {
  const [formData, setFormData] = useState({
    userType: 'client',
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: '',
    roleEmploye: 'Administrateur'
  });
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');
    const { firstName, lastName, email, password, confirmPassword, userType, roleEmploye } = formData;

    if (!firstName || !lastName || !email || !password || !confirmPassword) {
      setErrorMsg("Tous les champs sont obligatoires");
      return;
    }

    if (password !== confirmPassword) {
      setErrorMsg("Les mots de passe ne correspondent pas.");
      return;
    }

    if (password.length < 8) {
      setErrorMsg("Le mot de passe doit contenir au moins 8 caractères.");
      return;
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

      console.log('Envoi des données au backend:', data);
      
      const response = await api.post(
        `/${userType}/register/`,
        data
      );
      
      console.log('Réponse du backend:', response.data);
      setSuccessMsg("Inscription réussie ! Redirection vers la page de connexion...");
      setTimeout(() => navigate('/auth/login'), 2000);
    } catch (error) {
      console.error('Erreur lors de l\'inscription:', error);
      
      // Afficher les erreurs détaillées du backend si disponibles
      if (error.response?.data) {
        const { data } = error.response;
        
        // Si c'est un objet d'erreurs (comme un serializer error de Django)
        if (typeof data === 'object' && !Array.isArray(data) && data !== null) {
          const errorMessages = Object.entries(data)
            .map(([field, errors]) => {
              // Si c'est une liste d'erreurs pour un champ
              if (Array.isArray(errors)) {
                return `${field}: ${errors.join(', ')}`;
              }
              // Si c'est une erreur simple
              return `${field}: ${errors}`;
            })
            .join('\n');
          setErrorMsg(errorMessages);
        } 
        // Si c'est une chaîne simple
        else if (typeof data === 'string') {
          setErrorMsg(data);
        }
        // Si c'est un tableau d'erreurs
        else if (Array.isArray(data)) {
          setErrorMsg(data.join('\n'));
        }
        // Si c'est un objet avec un champ 'detail' ou 'message'
        else if (data.detail || data.message) {
          setErrorMsg(data.detail || data.message);
        }
        // Autre format inattendu
        else {
          setErrorMsg('Une erreur inattendue est survenue lors de l\'inscription.');
        }
      } else {
        setErrorMsg(error.message || "Une erreur est survenue lors de l'inscription");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="container mt-5">
      <div className="row justify-content-center">
        <div className="col-lg-8 col-xl-7">
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
                  >Client</NavLink>
                </NavItem>
                <NavItem>
                  <NavLink
                    className={classnames({ active: formData.userType === 'employee' })}
                    href="#pablo"
                    onClick={e => {
                      e.preventDefault();
                      setFormData(prev => ({ ...prev, userType: 'employee' }));
                    }}
                  >Employé</NavLink>
                </NavItem>
              </Nav>
            </CardHeader>

            <CardBody className="px-lg-5 py-lg-4">
              {errorMsg && <Alert color="danger">{errorMsg}</Alert>}
              {successMsg && <Alert color="success">{successMsg}</Alert>}

              <Form role="form" onSubmit={handleSubmit}>
                <Row>
                  <Col md="6">
                    <FormGroup>
                      <InputGroup className="input-group-alternative mb-3">
                        <InputGroupAddon addonType="prepend">
                          <InputGroupText><i className="ni ni-single-02" /></InputGroupText>
                        </InputGroupAddon>
                        <Input
                          placeholder="Prénom"
                          type="text"
                          name="firstName"
                          value={formData.firstName}
                          onChange={handleChange}
                          required
                        />
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
                        />
                      </InputGroup>
                    </FormGroup>
                  </Col>
                </Row>

                <FormGroup>
                  <InputGroup className="input-group-alternative mb-3">
                    <InputGroupAddon addonType="prepend">
                      <InputGroupText><i className="ni ni-email-83" /></InputGroupText>
                    </InputGroupAddon>
                    <Input
                      placeholder="Email"
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      required
                    />
                  </InputGroup>
                </FormGroup>

                <Row>
                  <Col md="6">
                    <FormGroup>
                      <InputGroup className="input-group-alternative">
                        <InputGroupAddon addonType="prepend">
                          <InputGroupText><i className="ni ni-lock-circle-open" /></InputGroupText>
                        </InputGroupAddon>
                        <Input
                          placeholder="Mot de passe"
                          type="password"
                          name="password"
                          value={formData.password}
                          onChange={handleChange}
                          required
                        />
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
                        />
                      </InputGroup>
                    </FormGroup>
                  </Col>
                </Row>

                {formData.userType === 'employee' && (
                  <FormGroup>
                    <InputGroup className="input-group-alternative mb-3">
                      <InputGroupAddon addonType="prepend">
                        <InputGroupText><i className="ni ni-badge" /></InputGroupText>
                      </InputGroupAddon>
                      <Input
                        type="select"
                        name="roleEmploye"
                        value={formData.roleEmploye}
                        onChange={handleChange}
                      >
                        <option value="Administrateur">Administrateur</option>
                        <option value="Gestionnaire">Gestionnaire</option>
                      </Input>
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
        </div>
      </div>
    </div>
  );
};

export default Register;
