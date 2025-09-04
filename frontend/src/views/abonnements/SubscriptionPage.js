import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Card, 
  CardHeader, 
  CardBody, 
  CardTitle, 
  CardText,
  Row, 
  Col, 
  Form, 
  FormGroup,
  Label, 
  Input, 
  Button, 
  Alert, 
  Spinner, 
  Container,
  Badge
} from 'reactstrap';
import subscriptionService from '../../services/subscriptionService';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import abonnementService from '../../services/abonnementService';

const SubscriptionPage = () => {
  const navigate = useNavigate();
  
  // État du formulaire
  const [formData, setFormData] = useState({
    type_abonnement: ''
  });
  
  const [formErrors, setFormErrors] = useState({});
  const [userData, setUserData] = useState({
    id: '',
    nom: '',
    prenom: '',
    email: ''
  });
  
  const [loading, setLoading] = useState(true);
  const [isRequestPending, setIsRequestPending] = useState(false);
  const [currentSubscription, setCurrentSubscription] = useState({
    type: '',
    status: '',
    expiryDate: ''
  });

  // Constantes
  const ABONNEMENT_TYPES = {
    BASIC: 'BASIC',
    PRO: 'PRO',
    ENTERPRISE: 'ENTERPRISE'
  };

  const ABONNEMENT_DESCRIPTIONS = {
    'BASIC': 'Parfait pour commencer',
    'PRO': 'Idéal pour les petites équipes',
    'ENTERPRISE': 'Pour les entreprises en croissance'
  };

  const abonnementOptions = [
    { 
      value: ABONNEMENT_TYPES.BASIC, 
      title: 'BASIC',
      description: 'Parfait pour commencer',
      features: [
        'Accès aux fonctionnalités de base',
        '1 utilisateur',
        'Support par email',
        'Pas de membres invités'
      ],
      buttonText: 'Sélectionner',
      popular: false
    },
    { 
      value: ABONNEMENT_TYPES.PRO, 
      title: 'PRO',
      description: 'Idéal pour les petites équipes',
      features: [
        'Toutes les fonctionnalités BASIC',
        'Jusqu\'à 3 utilisateurs',
        'Support prioritaire',
        'Jusqu\'à 2 membres invités',
        'Rapports avancés'
      ],
      buttonText: 'Sélectionner',
      popular: true
    },
    { 
      value: ABONNEMENT_TYPES.ENTERPRISE, 
      title: 'ENTERPRISE',
      description: 'Pour les entreprises en croissance',
      features: [
        'Toutes les fonctionnalités PRO',
        'Utilisateurs illimités',
        'Support 24/7',
        'Membres illimités',
        'Rapports personnalisés',
        'Intégrations avancées'
      ],
      buttonText: 'Sélectionner',
      popular: false
    }
  ];
  
  // Sélection d'un abonnement
  const selectSubscription = (type) => {
    setFormData({
      type_abonnement: type
    });
    
    if (formErrors.type_abonnement) {
      setFormErrors(prev => ({
        ...prev,
        type_abonnement: ''
      }));
    }
  };

  // Gestion des changements du formulaire
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prevState => ({
      ...prevState,
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

    if (!formData.type_abonnement) {
      errors.type_abonnement = 'Veuillez sélectionner un type d\'abonnement';
    } else if (!Object.values(ABONNEMENT_TYPES).includes(formData.type_abonnement)) {
      errors.type_abonnement = 'Veuillez sélectionner un type d\'abonnement valide';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Fonction pour activer/désactiver l'abonnement
  const handleToggleStatus = async (activate) => {
    if (!currentSubscription?.id) {
      toast.error('Impossible de trouver l\'abonnement à modifier');
      return;
    }

    setLoading(true);
    try {
      await abonnementService.toggle(currentSubscription.id);
      
      // Mettre à jour l'état local avec le nouveau statut
      setCurrentSubscription(prev => ({
        ...prev,
        is_active: activate
      }));
      
      toast.success(`Abonnement ${activate ? 'activé' : 'désactivé'} avec succès`);
    } catch (error) {
      console.error('Erreur lors du changement de statut:', error);
      toast.error(error.message || 'Une erreur est survenue lors de la mise à jour du statut');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const fetchUserAndSubscription = async () => {
      try {
        setLoading(true);
        
        // Récupérer les données de l'utilisateur connecté
        const token = localStorage.getItem('token');
        if (token) {
          try {
            const decodedToken = parseJwt(token);
            if (decodedToken) {
              const user = {
                id: decodedToken.user_id || '',
                nom: decodedToken.last_name || '',
                prenom: decodedToken.first_name || '',
                email: decodedToken.email || ''
              };
              setUserData(user);
              
              // Récupérer l'abonnement du client
              if (user.id) {
                const subscription = await subscriptionService.getClientSubscriptionType(user.id);
                if (subscription) {
                  setCurrentSubscription({
                    id: subscription.id_abonnement || subscription.id, // Utiliser id_abonnement si disponible, sinon id
                    type: subscription.type_abonnement || 'BASIC',
                    is_active: subscription.is_active || false, // Ajouter le statut actif
                    status: subscription.is_active ? 'Actif' : 'Inactif',
                    expiryDate: subscription.date_expiration || '',
                    date_creation: subscription.date_creation || ''
                  });
                }
              }
            }
          } catch (error) {
            console.error('Erreur lors du chargement des données:', error);
            toast.error('Erreur lors du chargement des données de l\'utilisateur');
          }
        }
      } catch (error) {
        console.error('Erreur:', error);
        toast.error('Impossible de charger les données utilisateur');
      } finally {
        setLoading(false);
      }
    };
    
    fetchUserAndSubscription();
  }, []);


  // Fonction utilitaire pour parser le JWT
  const parseJwt = (token) => {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch (e) {
      console.error('Erreur lors du décodage du token:', e);
      return null;
    }
  };


  // Styles utilitaires pour un rendu plus moderne
  const getCardStyle = (option, isSelected, isCurrentPlan) => {
    const base = {
      borderRadius: 20,
      transition: 'transform 0.2s, box-shadow 0.2s, border-color 0.2s, background-color 0.2s',
      boxShadow: '0 8px 24px rgba(0,0,0,0.06)',
      cursor: 'pointer',
      border: '1px solid rgba(0,0,0,0.08)'
    };
    const states = {};
    if (option.popular) {
      states.borderColor = '#5e72e4';
      states.boxShadow = '0 10px 28px rgba(94,114,228,0.18)';
    }
    if (isCurrentPlan) {
      states.borderColor = '#28c76f';
      states.boxShadow = '0 10px 28px rgba(40,199,111,0.18)';
    }
    if (isSelected) {
      states.transform = 'translateY(-6px)';
      states.boxShadow = '0 14px 32px rgba(0,0,0,0.14)';
      states.borderColor = '#5e72e4';
      states.backgroundColor = 'rgba(94,114,228,0.06)';
    }
    return { ...base, ...states };
  };



  // Soumission du formulaire
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      if (!formData.type_abonnement) {
        toast.error('Veuillez sélectionner un type d\'abonnement');
        return;
      }

      const token = localStorage.getItem('token');
      const endpoint = currentSubscription 
        ? 'http://localhost:8000/abonnements/update-request/'
        : 'http://localhost:8000/client/subscribe/';
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          type_abonnement: formData.type_abonnement
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Erreur lors de l\'envoi de la demande de modification');
      }

      const data = await response.json();
      toast.success(data.message || 'Votre demande de modification a été envoyée à l\'administrateur');
      
      // Update UI to show pending status
      if (currentSubscription) {
        setCurrentSubscription({
          ...currentSubscription,
          status: 'En attente de validation',
          pendingType: formData.type_abonnement
        });
      } else {
        // Nouvel abonnement
        setCurrentSubscription({
          type: formData.type_abonnement,
          status: 'en_attente'
        });
        toast.success('Votre abonnement a été créé avec succès !');
      }
      
      setFormData({
        type_abonnement: ''
      });
      
      // Rediriger vers la page de gestion d'équipe après 1,5 secondes
      setTimeout(() => {
        navigate('/client/manage-team');
      }, 1500);
      
    } catch (error) {
      console.error('Erreur:', error);
      toast.error('Une erreur est survenue. Veuillez réessayer plus tard.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="content">
        <Container>
          <Row className="justify-content-center">
            <Col md="8">
              <Card>
                <CardBody className="text-center p-5">
                  <Spinner color="primary" />
                  <p className="mt-3">Chargement de votre abonnement...</p>
                </CardBody>
              </Card>
            </Col>
          </Row>
        </Container>
      </div>
    );
  }



  // Rendu des cartes d'abonnement
  const renderSubscriptionCards = () => {
    return (
      <Row className="justify-content-center">
        {abonnementOptions.map((option) => {
          const isCurrentPlan = currentSubscription && currentSubscription.type === option.value;
          const isSelected = formData.type_abonnement === option.value;
          
          return (
            <Col key={option.value} md="4" className="mb-5 d-flex">
              <Card 
                className={`h-100 w-100 ${option.popular ? 'border-primary' : ''} ${isCurrentPlan ? 'border-success' : ''}`}
                style={getCardStyle(option, isSelected, isCurrentPlan)}
                role="button"
                aria-pressed={isSelected}
                onClick={() => !isCurrentPlan && selectSubscription(option.value)}
              >
                {option.popular && (
                  <div className="text-center mt-3">
                    <span className="badge rounded-pill bg-primary" style={{ padding: '6px 12px' }}>Le plus populaire</span>
                  </div>
                )}
                
                <CardBody className="text-center p-4 d-flex flex-column">
                  <CardTitle tag="h4" className="mb-2" style={{ letterSpacing: 0.5 }}>
                    {option.title}
                    {isCurrentPlan && (
                      <>
                        <Badge color={currentSubscription.is_active ? "success" : "secondary"} className="ms-2">
                          {currentSubscription.is_active ? 'Actif' : 'Inactif'}
                        </Badge>
                        {currentSubscription.pendingType && (
                          <Badge color="warning" className="ms-1">
                            En attente
                          </Badge>
                        )}
                      </>
                    )}
                  </CardTitle>
                  <CardText className="text-muted mb-4" style={{ minHeight: 24 }}>{option.description}</CardText>
                  
                  {isCurrentPlan && (
                    <>
                      {currentSubscription.expiryDate && (
                        <div className="mb-3">
                          <small className="text-muted">
                            Valide jusqu'au {new Date(currentSubscription.expiryDate).toLocaleDateString('fr-FR')}
                          </small>
                        </div>
                      )}
                      {/* Activation/Deactivation buttons removed as per user request */}
                    </>
                  )}

                  <ul className="list-unstyled mb-4 text-start mx-auto" style={{ maxWidth: 260 }}>
                    {option.features.map((feature, index) => (
                      <li key={index} className="mb-2">
                        <i className="fas fa-check me-2" style={{ color: '#28c76f' }}></i>
                        {feature}
                      </li>
                    ))}
                  </ul>
                </CardBody>
              </Card>
            </Col>
          );
        })}
      </Row>
    );
  };

  // Rendu du composant
  const renderContent = () => {
    if (isRequestPending) {
      return (
        <Alert color="info" className="mb-4">
          Votre demande de changement d'abonnement est en attente de validation par l'administrateur.
        </Alert>
      );
    }

    return (
      <div>
        {currentSubscription && (
          <Alert className="mb-4" style={{ backgroundColor: '#0a2540', color: '#fff', borderColor: '#0a2540' }}>
            <h4 className="alert-heading">Votre abonnement actuel</h4>
            <p>Type: <strong>{currentSubscription.type}</strong></p>
            <p>Statut: <strong style={{ color: '#ffffff' }}>
              {currentSubscription.is_active ? 'Actif' : 'Inactif'}
            </strong></p>
          </Alert>
        )}
        
        <Form onSubmit={handleSubmit}>
          {renderSubscriptionCards()}
          
          {formData.type_abonnement && (
            <div className="text-center mt-4">
              <Button 
                color="primary" 
                type="submit" 
                disabled={loading}
                size="lg"
              >
                {loading ? (
                  <span>
                    <Spinner size="sm" className="me-2" />
                    Traitement en cours...
                  </span>
                ) : (
                  `Changer pour ${formData.type_abonnement}`
                )}
              </Button>
            </div>
          )}
        </Form>
      </div>
    );
  };

  return (
    <>
      <div className="header bg-gradient-info pb-8 pt-5 pt-md-8">
        <Container fluid>
          <div className="header-body">
            <Row className="align-items-center">
              <Col>
                <h2 className="text-white mb-0">Abonnement</h2>
                <p className="text-white mt-2 mb-0">
                  {currentSubscription
                    ? 'Consultez votre abonnement et envoyez une demande de changement si nécessaire.'
                    : 'Choisissez le plan qui correspond à vos besoins.'}
                </p>
              </Col>
            </Row>
          </div>
        </Container>
      </div>
      <Container className="mt--7" fluid>
        <Row className="justify-content-center">
          <Col md="8">
            <Card className="shadow">
              <CardHeader className="border-0">
               
                
              </CardHeader>
              <CardBody>
                {renderContent()}
              </CardBody>
            </Card>
          </Col>
        </Row>
      </Container>
    </>
  );
};

export default SubscriptionPage;