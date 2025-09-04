import React, { useState } from "react";
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
  Alert,
  Spinner,
} from "reactstrap";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import authService from "../../services/auth";



const ValidateGcsUri = () => {
  const [formData, setFormData] = useState({ 
    uri: "", 
    serviceAccountEmail: "" 
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [formErrors, setFormErrors] = useState({});
  const navigate = useNavigate();

  // Email de l'utilisateur connecté
  const email = authService.getCurrentUser()?.email || "";

  // Gestion du changement des champs
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    if (formErrors[name]) {
      setFormErrors((prev) => ({ ...prev, [name]: null }));
    }
    if (error) setError("");
  };
const handleSubmit = async (e) => {
  e.preventDefault();
  setError("");
  setFormErrors({});
  setLoading(true);

  // Validation des champs
  const errors = {};
  if (!formData.uri) {
    errors.uri = "L'URI GCS est requise";
  } else if (!formData.uri.startsWith("gs://")) {
    errors.uri = "L'URI doit commencer par gs://";
  }

  if (!formData.serviceAccountEmail) {
    errors.serviceAccountEmail = "L'email du compte de service est requis";
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.serviceAccountEmail)) {
    errors.serviceAccountEmail = "Format d'email invalide";
  }

    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      setLoading(false);
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${process.env.REACT_APP_API_URL || ''}/validate-gcs-uri/`,
        {
          uri: formData.uri.trim(),
          email: formData.serviceAccountEmail.trim().toLowerCase(),
        },
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            'X-Requested-With': 'XMLHttpRequest'
          },
          withCredentials: true // Important pour les cookies de session
        }
      );

      // Si la requête a réussi, on redirige vers la page de succès
      // avec les données de la réponse
      const successData = response.data.data || response.data;
      
      // Stockez les données dans le state de navigation pour les récupérer sur la page de succès
      navigate('/client/validation-success', { 
        state: { 
          success: true,
          data: successData
        },
        replace: true
      });
      
    } catch (error) {
      console.error('Erreur lors de la validation GCS:', error);
      let errorMessage = 'Erreur lors de la validation GCS';
      
      if (error.response) {
        // Gestion des erreurs spécifiques
        if (error.response.status === 401) {
          // Redirection vers la page de connexion si non authentifié
          authService.logout();
          navigate('/login', { 
            state: { 
              from: '/validate-gcs-uri',
              error: 'Votre session a expiré. Veuillez vous reconnecter.'
            } 
          });
          return;
        }
        
        // Récupération du message d'erreur du serveur
        errorMessage = error.response.data?.error || 
                     error.response.data?.message || 
                     `Erreur serveur (${error.response.status})`;
                     
      } else if (error.request) {
        // Le serveur n'a pas répondu
        errorMessage = "Pas de réponse du serveur. Vérifiez votre connexion internet.";
      } else {
        // Erreur lors de la configuration de la requête
        errorMessage = `Erreur de configuration de la requête: ${error.message}`;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <>
      <div className="header bg-gradient-info pb-8 pt-5 pt-md-8">
        <Container fluid>
          <div className="header-body">
            <h2 className="text-white">Connexion Google Cloud Storage</h2>
            <p className="text-white-50">
              Connectez votre espace de stockage Google Cloud pour importer vos données Play Console.
              L'accès sera vérifié pour votre compte EasyAppReport :{" "}
              <strong>{email || "non connecté"}</strong>.
            </p>
          </div>
        </Container>
      </div>

      <Container className="mt--8 pb-5">
        <Row className="justify-content-center">
          <Col lg="6" md="8">
            <Card className="bg-secondary shadow border-0">
              <CardHeader className="bg-transparent pb-5">
                
                <div className="text-center">
                  <h1>Configuration du stockage Google Cloud
                  </h1>
                  <p className="text-lead">
                    Veuillez entrer les informations de votre bucket Google Cloud Storage.
                    
                  </p>
                </div>
              </CardHeader>
              <CardBody className="px-lg-5 py-lg-5">
                <div className="text-center text-muted mb-4">
                  <small>Entrez les détails de votre bucket GCS</small>
                </div>
                <Form role="form" onSubmit={handleSubmit}>
                  {error && (
                    <Alert color="danger" className="text-center">
                      <strong>Erreur:</strong> {error}
                    </Alert>
                  )}

                  <FormGroup className={formErrors.uri ? "has-danger" : "mb-3"}>
                    <label className="form-control-label" htmlFor="uri">
                      URI GCS <span className="text-danger">*</span>
                    </label>
                    <Input
                      className={`form-control-alternative ${formErrors.uri ? 'is-invalid' : ''}`}
                      id="uri"
                      name="uri"
                      placeholder="gs://votre-bucket/rapports"
                      type="text"
                      value={formData.uri}
                      onChange={handleChange}
                      disabled={loading}
                    />
                    {formErrors.uri && (
                      <div className="invalid-feedback d-block">{formErrors.uri}</div>
                    )}
                    <small className="form-text text-muted">
                      L'URI GCS de votre bucket (commence par gs://)
                    </small>
                  </FormGroup>

                  <FormGroup className={formErrors.serviceAccountEmail ? "has-danger" : "mb-4"}>
                    <label className="form-control-label" htmlFor="serviceAccountEmail">
                      Email du compte de service <span className="text-danger">*</span>
                    </label>
                    <Input
                      className={`form-control-alternative ${formErrors.serviceAccountEmail ? 'is-invalid' : ''}`}
                      id="serviceAccountEmail"
                      name="serviceAccountEmail"
                      placeholder="votre-compte@votredomaine.com"
                      type="email"
                      value={formData.serviceAccountEmail}
                      onChange={handleChange}
                      disabled={loading}
                    />
                    {formErrors.serviceAccountEmail && (
                      <div className="invalid-feedback d-block">{formErrors.serviceAccountEmail}</div>
                    )}
                    <small className="form-text text-muted">
                      L'email du compte de service avec accès au bucket
                    </small>
                  </FormGroup>

                  <div className="text-center">
                    <Button 
                      className="my-4" 
                      color="primary" 
                      type="submit" 
                      disabled={loading}
                    >
                      {loading ? (
                        <>
                          <Spinner size="sm" className="mr-2" />
                          Validation en cours...
                        </>
                      ) : (
                        "Valider la configuration"
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

export default ValidateGcsUri;