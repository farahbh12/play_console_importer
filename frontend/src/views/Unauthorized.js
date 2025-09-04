import React, { useEffect, useCallback } from 'react';
import { Card, CardBody, CardHeader, Container, Row, Col, Button } from 'reactstrap';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Unauthorized = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  // Déterminer le tableau de bord par défaut en fonction du rôle de l'utilisateur
  const getDashboardPath = useCallback(() => {
    if (!user) return '/auth/login';
    
    if (user.is_superuser || user.user_type === 'employee') {
      return '/admin/profile';
    } else if (user.user_type === 'client') {
      return '/client/profile';
    }
    
    return '/auth/login';
  }, [user]);

  // Rediriger automatiquement après un délai
  useEffect(() => {
    const timer = setTimeout(() => {
      navigate(getDashboardPath());
    }, 5000); // Rediriger après 5 secondes
    
    return () => clearTimeout(timer);
  }, [navigate, user, getDashboardPath]);

  return (
    <div className="main-content">
      <Container className="mt--8 pb-5">
        <Row className="justify-content-center">
          <Col lg="6">
            <Card className="bg-secondary shadow border-0">
              <CardHeader className="bg-transparent pb-5">
                <div className="text-muted text-center mt-2 mb-3">
                  <h1>Accès Refusé</h1>
                </div>
              </CardHeader>
              <CardBody className="px-lg-5 py-lg-5">
                <div className="text-center text-muted mb-4">
                  <p>Désolé, vous n'avez pas les autorisations nécessaires pour accéder à cette page.</p>
                  <p>Vous serez redirigé automatiquement vers votre tableau de bord dans quelques secondes.</p>
                  <p>Si la redirection ne fonctionne pas, cliquez sur le bouton ci-dessous :</p>
                </div>
                <div className="text-center">
                  <Button 
                    tag={Link} 
                    to={getDashboardPath()} 
                    color="primary" 
                    className="my-4"
                  >
                    Retour au tableau de bord
                  </Button>
                </div>
              </CardBody>
            </Card>
          </Col>
        </Row>
      </Container>
    </div>
  );
};

export default Unauthorized;
