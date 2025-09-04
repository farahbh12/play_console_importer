import React, { useState } from 'react';
import { Card, CardBody, CardTitle, CardText, Button, Row, Col } from 'reactstrap';
import { toast } from 'react-toastify';
import { useNavigate } from 'react-router-dom';

const ABONNEMENT_OPTIONS = [
  {
    id: 'BASIC',
    title: 'Basic',
    price: '9.99€',
    description: 'Parfait pour les débutants',
    features: [
      '1 compte utilisateur',
      'Accès de base aux fonctionnalités',
      'Support par email',
      'Mises à jour de sécurité',
    ],
  },
  {
    id: 'PRO',
    title: 'Professionnel',
    price: '29.99€',
    description: 'Idéal pour les professionnels',
    popular: true,
    features: [
      '5 comptes utilisateurs',
      'Toutes les fonctionnalités Basic',
      'Support prioritaire',
      'Rapports avancés',
      'Formation en ligne',
    ],
  },
  {
    id: 'ENTERPRISE',
    title: 'Entreprise',
    price: '99.99€',
    description: 'Solution complète pour entreprises',
    features: [
      'Comptes illimités',
      'Toutes les fonctionnalités Pro',
      'Support 24/7',
      'Personnalisation avancée',
      'Intégrations API',
    ],
  },
];

const SubscriptionSelection = ({ userData, onComplete }) => {
  // Hooks must be called at the top level
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  
  // Debug log
  console.log('SubscriptionSelection - userData:', userData);
  
  // Early return after hooks
  if (!userData) {
    console.error('userData is undefined in SubscriptionSelection');
    return <div className="alert alert-danger">Erreur: Données utilisateur manquantes</div>;
  }

  const handleSelectPlan = async (planId) => {
    setSelectedPlan(planId);
  };

  const handleSubmit = async () => {
    setIsProcessing(true);
    setError('');
    
    try {
      const url = `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/client/activate-account/`;
      console.log('Sending activation request to:', url);
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          user_id: userData.id,
          subscription_type: selectedPlan,
        }),
      });

      const data = await response.json();
      console.log('Activation response:', data);

      if (!response.ok) {
        throw new Error(data.error || 'Failed to activate account');
      }

      // Handle success
      toast.success('Compte activé avec succès!');
      
      // Call the onComplete callback with the subscription data
      if (onComplete) {
        onComplete(data);
      }
      
      // Redirect to login
      setTimeout(() => navigate('/auth/login'), 2000);
    } catch (error) {
      console.error('Activation error:', error);
      setError(error.message || 'Une erreur est survenue lors de l\'activation du compte');
      toast.error(error.message || 'Une erreur est survenue');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="subscription-selection">
      <h2 className="text-center mb-3">Choisissez votre abonnement</h2>
      <p className="text-center text-muted mb-5">
        Sélectionnez le type d'abonnement qui correspond le mieux à vos besoins.
        <br />
        <span className="text-danger">*</span> Champs obligatoires
      </p>
      
      {!selectedPlan && (
        <div className="alert alert-warning text-center">
          <i className="fas fa-exclamation-triangle me-2"></i>
          Veuillez sélectionner un type d'abonnement pour continuer
        </div>
      )}
      
      <Row className="justify-content-center">
        {ABONNEMENT_OPTIONS.map((plan) => (
          <Col key={plan.id} md="4" className="mb-4">
            <Card 
              className={`h-100 ${selectedPlan === plan.id ? 'border-primary shadow-lg' : 'border-light'} ${plan.popular ? 'border-success' : ''}`}
              style={{
                cursor: 'pointer',
                borderWidth: selectedPlan === plan.id ? '3px' : '1px',
                transition: 'all 0.3s ease',
                transform: selectedPlan === plan.id ? 'translateY(-5px)' : 'none',
                opacity: selectedPlan && selectedPlan !== plan.id ? '0.8' : '1'
              }}
              onClick={() => handleSelectPlan(plan.id)}
            >
              {plan.popular && (
                <div className="text-center mt-2">
                  <span className="badge bg-success">Populaire</span>
                </div>
              )}
              <CardBody className="text-center">
                <CardTitle tag="h4">{plan.title}</CardTitle>
                <h3 className="my-3">{plan.price}<small className="text-muted">/mois</small></h3>
                <CardText className="text-muted mb-4">{plan.description}</CardText>
                <ul className="list-unstyled text-start ms-4">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="mb-2">
                      <i className="fas fa-check text-success me-2"></i>
                      {feature}
                    </li>
                  ))}
                </ul>
                <Button 
                  color={selectedPlan === plan.id ? 'primary' : 'outline-primary'}
                  className="mt-3"
                  block
                >
                  {selectedPlan === plan.id ? 'Sélectionné' : 'Sélectionner'}
                </Button>
              </CardBody>
            </Card>
          </Col>
        ))}
      </Row>

      <div className="text-center mt-5">
        <Button 
          color="primary" 
          size="lg" 
          onClick={handleSubmit}
          disabled={!selectedPlan || isProcessing}
        >
          {isProcessing ? 'Traitement...' : 'Valider mon abonnement'}
        </Button>
      </div>
      {error && (
        <div className="alert alert-danger mt-3">
          {error}
        </div>
      )}
    </div>
  );
};

export default SubscriptionSelection;
