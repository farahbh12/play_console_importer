import React, { useState, useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../../contexts/AuthContext';
import {
  Button,
  Card,
  CardHeader,
  CardBody,
  FormGroup,
  Form,
  Input,
  InputGroupAddon,
  InputGroupText,
  InputGroup,
  Row,
  Col,
  Alert,
  CardFooter
} from "reactstrap";

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [userType, setUserType] = useState('client');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const navigate = useNavigate();
  const { login } = useContext(AuthContext);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    // Validation des champs
    if (!email || !password) {
      setError('Veuillez remplir tous les champs');
      return;
    }
    
    setLoading(true);

    try {
      console.log('Tentative de connexion avec:', { email, userType });
      
      // Appel à la fonction de connexion du contexte
      const result = await login(email, password, userType);
      
      console.log('Résultat de la connexion:', result);
      
      // Le contexte retourne un objet avec user et redirectPath
      if (result && result.redirectPath) {
        console.log('Redirection vers:', result.redirectPath);
        // Utiliser navigate au lieu de window.location pour une navigation SPA propre
        navigate(result.redirectPath, { replace: true });
      } else {
        // Fallback: déterminer la redirection basée sur le type d'utilisateur
        const redirectPath = userType === 'client' ? '/client/dashboard' : '/admin/index';
        console.log('Redirection fallback vers:', redirectPath);
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
      
      if (err.response?.data) {
        const { data } = err.response;
        
        // Erreurs de validation du backend
        if (data.non_field_errors) {
          errorMessage = data.non_field_errors.join(' ');
        } else if (data.detail) {
          errorMessage = data.detail;
        } else if (data.email) {
          errorMessage = `Email: ${data.email[0]}`;
        } else if (data.password) {
          errorMessage = `Mot de passe: ${data.password[0]}`;
        }
      }
      
      setError(errorMessage);
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
              <div className="text-center">
                <Button
                  color={userType === 'client' ? 'primary' : 'secondary'}
                  onClick={() => setUserType('client')}
                  className="mr-2"
                >
                  Client
                </Button>
                <Button
                  color={userType === 'employee' ? 'primary' : 'secondary'}
                  onClick={() => setUserType('employee')}
                >
                  Employé
                </Button>
              </div>
            </CardHeader>
            
            <CardBody className="px-lg-5 py-lg-4">
              {error && (
                <Alert color="danger" className="alert-dismissible fade show" role="alert">
                  <span className="alert-icon"><i className="ni ni-notification-70"></i></span>
                  <span className="alert-text">{error}</span>
                  <button type="button" className="close" onClick={() => setError('')}>
                    <span aria-hidden="true">&times;</span>
                  </button>
                </Alert>
              )}
              
              <Form role="form" onSubmit={handleSubmit}>
                <FormGroup className="mb-3">
                  <InputGroup className="input-group-alternative">
                    <InputGroupAddon addonType="prepend">
                      <InputGroupText>
                        <i className="ni ni-email-83" />
                      </InputGroupText>
                    </InputGroupAddon>
                    <Input
                      placeholder="Email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      autoComplete="email"
                      required
                    />
                  </InputGroup>
                </FormGroup>
                
                <FormGroup>
                  <InputGroup className="input-group-alternative">
                    <InputGroupAddon addonType="prepend">
                      <InputGroupText>
                        <i className="ni ni-lock-circle-open" />
                      </InputGroupText>
                    </InputGroupAddon>
                    <Input
                      placeholder="Mot de passe"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      autoComplete="current-password"
                      required
                    />
                  </InputGroup>
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