import React, { useState, useContext } from 'react';
import { toast } from 'react-toastify';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../../contexts/AuthContext';
import classnames from 'classnames';
import {
  Button,
  Card,
  CardHeader,
  CardBody,
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
  CardFooter,
  FormFeedback
} from "reactstrap";

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [userType, setUserType] = useState('client');
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const navigate = useNavigate();
  const { login } = useContext(AuthContext);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const form = e.currentTarget;
    // Déclencher la validation HTML5 native si des champs requis sont vides/invalides
    if (form && typeof form.checkValidity === 'function' && !form.checkValidity()) {
      form.reportValidity?.();
      // Mettre à jour les erreurs locales également
      setFieldErrors({
        email: !email ? 'Email requis.' : '',
        password: !password ? 'Mot de passe requis.' : ''
      });
      return;
    }
    setError('');
    setFieldErrors({ email: '', password: '' });
    
    // Validation des champs
    let hasClientError = false;
    const nextFieldErrors = { email: '', password: '' };
    if (!email) { nextFieldErrors.email = 'Email requis.'; hasClientError = true; }
    if (!password) { nextFieldErrors.password = 'Mot de passe requis.'; hasClientError = true; }
    if (hasClientError) { setFieldErrors(nextFieldErrors); setError('Veuillez corriger les erreurs.'); return; }
    
    setLoading(true);

    try {

      
      // Appel à la fonction de connexion du contexte
      const result = await login(email, password, userType);
      

      
      // Le contexte retourne un objet avec user et redirectPath
      if (result && result.redirectPath) {

        // Utiliser navigate au lieu de window.location pour une navigation SPA propre
        navigate(result.redirectPath, { replace: true });
      } else {
        // Fallback: déterminer la redirection basée sur le type d'utilisateur
        const redirectPath = userType === 'client' ? '/client/profile' : '/admin/profile';

        navigate(redirectPath, { replace: true });
      }
      
    } catch (err) {
      console.error('Erreur lors de la connexion:', {
        message: err.message,
        response: err.response?.data,
        status: err.response?.status
      });
      
      // Gestion des erreurs spécifiques
      let errorMessage = 'Erreur lors de la connexion';
      const backend = err.response?.data;
      const fe = { email: '', password: '' };

      if (backend) {
        // 1) Normaliser les erreurs génériques
        const nonFieldRaw = backend.non_field_errors;
        let nfDetail = '';
        let nfCode = '';
        if (nonFieldRaw && typeof nonFieldRaw === 'object' && !Array.isArray(nonFieldRaw)) {
          nfDetail = nonFieldRaw.detail || '';
          nfCode = nonFieldRaw.code || nonFieldRaw.error_code || '';
        } else if (Array.isArray(nonFieldRaw)) {
          nfDetail = nonFieldRaw.join(' ');
        } else if (typeof nonFieldRaw === 'string') {
          nfDetail = nonFieldRaw;
        }

        const detailText = backend.detail ? String(backend.detail) : nfDetail || '';
        const code = backend.code || backend.error_code || nfCode;

        const invalidCred =
          /unable to log in/i.test(detailText)
          || /invalid credentials/i.test(detailText)
          || code === 'invalid_credentials';

        if (invalidCred) {
          fe.password = 'Mot de passe incorrect.';
          errorMessage = 'Email ou mot de passe incorrect.';
        }

        // 2) Mapping mismatch type de compte (client vs employé)
        const roleMismatch = backend.role_mismatch === true
          || backend.user_type_mismatch === true
          || code === 'ROLE_MISMATCH'
          || /type d'utilisateur/i.test(detailText)
          || /employee|employé|client/i.test(detailText) && /incorrect|mismatch|n'appartient pas|not/i.test(detailText);

        if (roleMismatch) {
          if (userType === 'client') {
            errorMessage = "Ce compte n'appartient pas à l'espace Client. Sélectionnez 'Employé'.";
          } else {
            errorMessage = "Ce compte n'appartient pas à l'espace Employé. Sélectionnez 'Client'.";
          }
        }

        if (backend.email) {
          fe.email = Array.isArray(backend.email) ? backend.email[0] : String(backend.email);
        }
        if (backend.password) {
          fe.password = Array.isArray(backend.password) ? backend.password[0] : String(backend.password);
        }
      } else if (err.message) {
        errorMessage = err.message;
        const msg = (err.message || '').toLowerCase();
        if (msg.includes('mot de passe') || msg.includes('password')) {
          fe.password = 'Mot de passe incorrect.';
          if (!errorMessage || !errorMessage.trim()) {
            errorMessage = 'Email ou mot de passe incorrect.';
          }
        }
      }

      // Fallbacks si aucun message n'a été déterminé
      const status = err.response?.status;
      if (!errorMessage || typeof errorMessage !== 'string' || errorMessage.trim() === '') {
        if (status === 401) {
          errorMessage = 'Email ou mot de passe incorrect.';
          if (!fe.password) fe.password = 'Mot de passe incorrect.';
        } else if (status === 400) {
          errorMessage = 'Requête invalide. Veuillez vérifier les champs.';
        } else {
          errorMessage = 'Erreur lors de la connexion. Veuillez réessayer.';
        }
      }

      setFieldErrors(fe);
      setError(String(errorMessage));
      try { window.scrollTo({ top: 0, behavior: 'smooth' }); } catch {}
      try { toast.error(String(errorMessage)); } catch {}
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mt-5">
      <div className="row justify-content-center">
        <div className="col-lg-8 col-xl-7">
          <Card className="bg-secondary shadow border-0 p-4">
            <CardHeader className="bg-transparent pb-4">
              <div className="text-center">
                <h2 className="text-dark">Connexion</h2>
                <p className="text-muted">Choisissez votre type d'utilisateur</p>
              </div>
              <Nav className="nav-fill mt-3" pills>
                <NavItem>
                  <NavLink
                    className={classnames({ active: userType === 'client' })}
                    href="#pablo"
                    onClick={e => {
                      e.preventDefault();
                      setUserType('client');
                    }}
                  >
                    Client
                  </NavLink>
                </NavItem>
                <NavItem>
                  <NavLink
                    className={classnames({ active: userType === 'employee' })}
                    href="#pablo"
                    onClick={e => {
                      e.preventDefault();
                      setUserType('employee');
                    }}
                  >
                    Employé
                  </NavLink>
                </NavItem>
              </Nav>
            </CardHeader>
            
            <CardBody className="px-lg-5 py-lg-4">
              {error && (
                <Alert color="danger" className="alert-dismissible fade show" role="alert">
                  <span className="alert-text">{error}</span>
                  <button type="button" className="close" onClick={() => setError('')}>
                    <span aria-hidden="true">&times;</span>
                  </button>
                </Alert>
              )}
              
              <Form role="form" onSubmit={handleSubmit}>
              <FormGroup className="mb-3">
  <InputGroup className="input-group-alternative">
    <InputGroupText>
      <i className="ni ni-email-83" />
    </InputGroupText>
    <Input
      placeholder="Email"
      type="email"
      value={email}
      onChange={(e) => {
        setEmail(e.target.value);
        if (e.target.value) {
          setFieldErrors(prev => ({ ...prev, email: '' }));
        }
      }}
      onBlur={() => {
        if (!email) {
          setFieldErrors(prev => ({ ...prev, email: 'Email requis.' }));
        }
      }}
      autoComplete="email"
      required
      invalid={!!fieldErrors.email}
      aria-invalid={!!fieldErrors.email}
    />
  </InputGroup>
  {fieldErrors.email ? (
    <FormFeedback className="d-block small mb-0">{fieldErrors.email}</FormFeedback>
  ) : null}
</FormGroup>

                
                <FormGroup>
                  <InputGroup className="input-group-alternative">
                    <InputGroupText>
                      <i className="ni ni-lock-circle-open" />
                    </InputGroupText>
                    <Input
                      placeholder="Mot de passe"
                      type="password"
                      value={password}
                      onChange={(e) => { setPassword(e.target.value); if (e.target.value) setFieldErrors(prev => ({ ...prev, password: '' })); }}
                      onBlur={() => { if (!password) setFieldErrors(prev => ({ ...prev, password: 'Mot de passe requis.' })); }}
                      autoComplete="current-password"
                      required
                      invalid={!!fieldErrors.password}
                      aria-invalid={!!fieldErrors.password}
                    />
                  </InputGroup>
                  {fieldErrors.password ? (
                    <FormFeedback className="d-block small mb-0">{fieldErrors.password}</FormFeedback>
                  ) : null}
                </FormGroup>
                
                <div className="custom-control custom-control-alternative custom-checkbox mb-3">
                  <input
                    className="custom-control-input"
                    id="customCheckLogin"
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                  />
                  <label className="custom-control-label" htmlFor="customCheckLogin">
                    <span className="text-muted">Se souvenir de moi</span>
                  </label>
                </div>
                
                <div className="text-center">
                  <Button 
                    className="my-4" 
                    color="primary" 
                    type="submit"
                    disabled={loading}
                    block
                  >
                    {loading ? (
                      <>
                        <span className="spinner-border spinner-border-sm mr-2" role="status"></span>
                        Connexion...
                      </>
                    ) : 'Se connecter'}
                  </Button>
                </div>
              </Form>
            </CardBody>
            
            <CardFooter className="bg-transparent">
              <Row>
                <Col xs="6">
                  <Link to="/auth/forgot-password" className="text-muted">
                    <small>Mot de passe oublié ?</small>
                  </Link>
                </Col>
                <Col className="text-right" xs="6">
                  <Link to="/auth/register" className="text-muted">
                    <small>Créer un compte</small>
                  </Link>
                </Col>
              </Row>
            </CardFooter>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Login;