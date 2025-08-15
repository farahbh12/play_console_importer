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
  InputGroupText,
  InputGroup,
  Row,
  Col,
  Alert,
  Nav,
  NavItem,
  NavLink,
  FormFeedback
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
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');
    setFieldErrors({ firstName: '', lastName: '', email: '', password: '', confirmPassword: '', roleEmploye: '' });
    const { firstName, lastName, email, password, confirmPassword, userType, roleEmploye } = formData;

    // Validation côté client
    let hasClientError = false;
    const nextFE = { firstName: '', lastName: '', email: '', password: '', confirmPassword: '', roleEmploye: '' };
    if (!firstName) { nextFE.firstName = 'Prénom requis.'; hasClientError = true; }
    if (!lastName) { nextFE.lastName = 'Nom requis.'; hasClientError = true; }
    if (!email) { nextFE.email = 'Email requis.'; hasClientError = true; }
    if (!password) { nextFE.password = 'Mot de passe requis.'; hasClientError = true; }
    if (!confirmPassword) { nextFE.confirmPassword = 'Confirmation requise.'; hasClientError = true; }
    if (password && password.length < 8) { nextFE.password = 'Minimum 8 caractères.'; hasClientError = true; }
    if (password && confirmPassword && password !== confirmPassword) { nextFE.confirmPassword = 'Les mots de passe ne correspondent pas.'; hasClientError = true; }
    if (hasClientError) { setFieldErrors(nextFE); setErrorMsg('Veuillez corriger les erreurs.'); return; }

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
      const backend = error.response?.data;
      if (backend) {
        // Mapper champs connus
        const fe = { firstName: '', lastName: '', email: '', password: '', confirmPassword: '', roleEmploye: '' };
        if (backend.first_name) fe.firstName = Array.isArray(backend.first_name) ? backend.first_name[0] : String(backend.first_name);
        if (backend.last_name) fe.lastName = Array.isArray(backend.last_name) ? backend.last_name[0] : String(backend.last_name);
        if (backend.email) fe.email = Array.isArray(backend.email) ? backend.email[0] : String(backend.email);
        if (backend.password) fe.password = Array.isArray(backend.password) ? backend.password[0] : String(backend.password);
        if (backend.password_confirm) fe.confirmPassword = Array.isArray(backend.password_confirm) ? backend.password_confirm[0] : String(backend.password_confirm);
        if (backend.role_employe) fe.roleEmploye = Array.isArray(backend.role_employe) ? backend.role_employe[0] : String(backend.role_employe);

        // Message global
        if (backend.detail) setErrorMsg(backend.detail);
        else if (backend.message) setErrorMsg(backend.message);
        else if (Object.keys(backend).length && !fe.email && !fe.password && !fe.firstName && !fe.lastName) {
          // Concaténer en message lisible en plus
          const msg = Object.entries(backend).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : String(v)}`).join('\n');
          setErrorMsg(msg);
        }
        setFieldErrors(fe);
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
                        <InputGroupText addonType="prepend">
                          <InputGroupText><i className="ni ni-single-02" /></InputGroupText>
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
                        {fieldErrors.firstName ? (<FormFeedback>{fieldErrors.firstName}</FormFeedback>) : null}
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
                        {fieldErrors.lastName ? (<FormFeedback>{fieldErrors.lastName}</FormFeedback>) : null}
                      </InputGroup>
                    </FormGroup>
                  </Col>
                </Row>

                <FormGroup>
                  <InputGroup className="input-group-alternative mb-3">
                    <InputGroupText addonType="prepend">
                      <InputGroupText><i className="ni ni-email-83" /></InputGroupText>
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
                    {fieldErrors.email ? (<FormFeedback>{fieldErrors.email}</FormFeedback>) : null}
                  </InputGroup>
                </FormGroup>

                <Row>
                  <Col md="6">
                    <FormGroup>
                      <InputGroup className="input-group-alternative">
                        <InputGroupText addonType="prepend">
                          <InputGroupText><i className="ni ni-lock-circle-open" /></InputGroupText>
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
                        {fieldErrors.password ? (<FormFeedback>{fieldErrors.password}</FormFeedback>) : null}
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
                        {fieldErrors.confirmPassword ? (<FormFeedback>{fieldErrors.confirmPassword}</FormFeedback>) : null}
                      </InputGroup>
                    </FormGroup>
                  </Col>
                </Row>

                {formData.userType === 'employee' && (
                  <FormGroup>
                    <InputGroup className="input-group-alternative mb-3">
                      <InputGroupText addonType="prepend">
                        <InputGroupText><i className="ni ni-badge" /></InputGroupText>
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
                      {fieldErrors.roleEmploye ? (<FormFeedback>{fieldErrors.roleEmploye}</FormFeedback>) : null}
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
