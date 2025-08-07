import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { 
  Container, 
  Row, 
  Col, 
  Card, 
  CardBody,
  Button,
  Alert,
  Spinner
} from "reactstrap";
import axios from "axios";
import authService from "../../services/auth";

const ValidationSuccess = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [validationData, setValidationData] = useState(null);
  const { state: locationState } = location;

  useEffect(() => {
    const fetchValidationData = async () => {
      try {
        // Vérifier d'abord si on a des données dans l'état de navigation
        if (locationState?.success && locationState.data) {
          console.log('Données de validation reçues via location.state:', locationState.data);
          setValidationData(locationState.data);
          setLoading(false);
          return;
        }

        // Si pas de données dans l'état, essayer de les récupérer depuis l'API
        const token = localStorage.getItem('token');
        if (!token) {
          throw new Error('Non authentifié');
        }

        console.log('Tentative de récupération des données depuis l\'API...');
        const response = await axios.get(
          `${process.env.REACT_APP_API_URL || ''}/validation-success/`,
          {
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
              'X-Requested-With': 'XMLHttpRequest'
            },
            withCredentials: true
          }
        );

        console.log('Réponse de l\'API:', response.data);
        if (response.data) {
          setValidationData(response.data);
        } else {
          setError("Aucune donnée de validation disponible.");
        }
      } catch (err) {
        console.error("Erreur lors de la récupération des données:", err);
        if (err.response?.status === 401) {
          authService.logout();
          navigate('/auth/login', { 
            state: { 
              from: '/admin/gcs/validation-success',
              error: 'Votre session a expiré. Veuillez vous reconnecter.'
            } 
          });
          return;
        }
        setError("Une erreur est survenue lors de la récupération des données de validation.");
      } finally {
        setLoading(false);
      }
    };

    fetchValidationData();
  }, [navigate, locationState]);

  if (loading) {
    return (
      <div className="text-center mt-5">
        <Spinner color="primary" />
        <p className="mt-2">Chargement des données de validation...</p>
      </div>
    );
  }


  if (error) {
    return (
      <Container className="mt-5">
        <Row className="justify-content-center">
          <Col md="8" lg="6">
            <Alert color="danger">
              <h4 className="alert-heading">Erreur</h4>
              <p>{error}</p>
              <hr />
              <Button color="primary" onClick={() => navigate('/admin/gcs/validate')}>
                Retour à la validation
              </Button>
            </Alert>
          </Col>
        </Row>
      </Container>
    );
  }

  if (!validationData) {
    return (
      <Container className="mt-5">
        <Row className="justify-content-center">
          <Col md="8" lg="6">
            <Alert color="warning">
              <h4 className="alert-heading">Aucune donnée de validation trouvée</h4>
              <p>Veuillez d'abord valider une configuration GCS.</p>
              <Button color="primary" onClick={() => navigate('/admin/gcs/validate')}>
                Aller à la validation
              </Button>
            </Alert>
          </Col>
        </Row>
      </Container>
    );
  }

  return (
    <Container className="mt-5">
      <Row className="justify-content-center">
        <Col md="8" lg="6">
          <Card className="shadow">
            <CardBody className="p-5">
              <div className="text-center">
                <div className="text-success mb-4" style={{ fontSize: '4rem' }}>
                  <i className="ni ni-check-bold" />
                </div>
                
                <h1 className="display-4 mb-3">Validation réussie !</h1>
                <p className="lead text-muted mb-4">
                  Votre configuration GCS a été validée avec succès.
                </p>
              </div>

              <div className="mt-4">
                <h5>Détails de la configuration :</h5>
                <ul className="list-unstyled">
                  <li><strong>Email du compte de service :</strong> {validationData.email}</li>
                  <li><strong>Bucket GCS :</strong> {validationData.bucket_name}</li>
                  
                </ul>
              </div>

              <div className="d-grid gap-2 d-md-flex justify-content-md-center mt-4">
                <Button
                  color="primary"
                  size="lg"
                  onClick={() => navigate('/admin/index')}
                  className="me-md-2"
                >
                  Tableau de bord
                </Button>
                <Button
                  color="secondary"
                  size="lg"
                  outline
                  onClick={() => navigate('/admin/gcs/display-files')}
                >
                  Afficher les rapports
                </Button>
              </div>
            </CardBody>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default ValidationSuccess;