// src/components/Headers/UserHeader.js
import React, { useState, useEffect } from "react";
import { Container, Row, Col, Button } from "reactstrap";
import authService from "../../services/auth";
import clientService from "../../services/clientService";

const UserHeader = () => {
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const currentUser = authService.getCurrentUser();

  useEffect(() => {
    const fetchUserData = async () => {
      setLoading(true);
      try {
        if (!currentUser) {
          console.log('No current user found');
          setUserData(null);
          return;
        }

        console.log('Current user type:', currentUser.user_type);
        
        if (currentUser.user_type === 'client') {
          try {
            // Pour les clients, essayer d'obtenir les données complètes via le service client
            const clientData = await clientService.getCurrent();
            console.log('Client data:', clientData);
            setUserData({ ...currentUser, ...clientData });
          } catch (clientError) {
            console.warn('Could not fetch full client data, using basic auth data', clientError);
            setUserData(currentUser);
          }
        } else if (currentUser.user_type === 'employee' || currentUser.employee_profile) {
          // Pour les employés, utiliser les données d'authentification de base
          console.log('Employee user detected, using auth data');
          setUserData(currentUser);
        } else {
          // Pour les autres types d'utilisateurs
          console.log('Other user type, using auth data');
          setUserData(currentUser);
        }
      } catch (error) {
        console.error("Error in fetchUserData:", error);
        setUserData(currentUser || null);
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, [currentUser]);

  const scrollToForm = () => {
    const formElement = document.getElementById('profile-form');
    if (formElement) {
      formElement.scrollIntoView({ behavior: 'smooth' });
    }
  };

  if (loading) {
    return <div>Chargement...</div>;
  }

  // Normalisation des données pour une meilleure affichage
  const displayName = userData?.user?.first_name || userData?.first_name || userData?.username || 'Utilisateur';
    // Construire le nom complet pour l'affichage
  const fullName = (userData?.first_name && userData?.last_name) 
    ? `${userData.first_name} ${userData.last_name}` 
    : 'Bienvenue sur votre espace client';
  
  return (
    <div
      className="header pb-8 pt-5 pt-lg-8 d-flex align-items-center"
      style={{
        minHeight: "400px",
        backgroundImage: "linear-gradient(87deg, #5e72e4 0, #825ee4 100%)",
        backgroundSize: "cover",
        backgroundPosition: "center top",
      }}
    >
      <span className="mask bg-gradient-default opacity-8" />
      <Container className="d-flex align-items-center" fluid>
        <Row>
          <Col lg="7" md="10">
            <h1 className="display-2 text-white">
              {userData ? `Bonjour ${displayName}` : 'Bonjour'}
            </h1>
            <p className="text-white mt-0 mb-4">
              {fullName}
            </p>
            {userData?.user_type === 'client' && userData?.abonnement && (
              <p className="text-white mb-4">
                <strong>Abonnement:</strong> {userData.abonnement.type} - {userData.abonnement.status}
              </p>
            )}
            <Button
              color="info"
              onClick={scrollToForm}
              className="mt-3"
            >
              Modifier mon profil
            </Button>
          </Col>
        </Row>
      </Container>
    </div>
  );
};

export default UserHeader;