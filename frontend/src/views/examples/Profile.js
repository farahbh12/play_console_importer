import React, { useState, useEffect } from 'react';
import {
  Badge,
  Button,
  Card,
  CardHeader,
  CardBody,
  FormGroup,
  Container,
  Row,
  Col,
  Alert
} from 'reactstrap';
import { Link } from 'react-router-dom';

import { useAuth } from '../../contexts/AuthContext';
import employeeService from '../../services/employeeService';

// Composant réutilisable pour afficher un champ
const ProfileField = ({ label, value, isBadge, color }) => (
  <Col lg="6">
    <FormGroup>
      <label className="form-control-label">{label}</label>
      {isBadge ? (
        <div>
          <Badge color={color}>{value}</Badge>
        </div>
      ) : (
        <p style={{ marginBottom: 0 }}>{value || 'Non défini'}</p>
      )}
    </FormGroup>
  </Col>
);

const Profile = () => {
  const { currentUser } = useAuth();
  const [userData, setUserData] = useState(null);
  const [userType, setUserType] = useState(''); // 'client' ou 'employee'
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

 // Récupération des données de l'employé
useEffect(() => {
  const fetchEmployeeData = async () => {
    try {
      setLoading(true);
      
      // Récupérer les données de l'employé connecté
      const employeeData = await employeeService.getCurrent();
      
      // Afficher les données dans la console pour débogage
      console.log('Données employé reçues:', employeeData);
      
      // Mettre à jour l'état avec les données de l'employé
      setUserData({
        // Données de base
        id: employeeData.id,
        first_name: employeeData.first_name || 'Non défini',
        last_name: employeeData.last_name || 'Non défini',
        email: employeeData.email || 'Non défini',
        
        // Récupération du rôle depuis role_employe
        role: employeeData.role_employe || 'Employé',
        
        // Dates
        date_joined: employeeData.date_joined,
        last_login: employeeData.last_login,
        
        // Statut
        is_active: employeeData.is_active !== undefined ? employeeData.is_active : true
      });
      
      setUserType('employee');
      
    } catch (error) {
      console.error('Erreur lors du chargement du profil employé:', error);
      setError(error.message || 'Impossible de charger le profil employé');
    } finally {
      setLoading(false);
    }
  };

  fetchEmployeeData();
}, []);
  // Formatage de la date
  const formatDate = (dateString) => {
    if (!dateString) return 'Non disponible';
    
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) {
        console.warn('Date invalide reçue:', dateString);
        return 'Date invalide';
      }
      
      return new Intl.DateTimeFormat('fr-FR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }).format(date);
      
    } catch (error) {
      console.error('Erreur de formatage de date:', error);
      return 'Format de date invalide';
    }
  };

  if (loading) {
    return (
      <div className="text-center my-5">
        <div className="spinner-border text-primary" role="status">
          <span className="sr-only">Chargement...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return <Container className="mt--7" fluid><Alert color="danger">{error}</Alert></Container>;
  }

  if (!userData) {
    return <Container className="mt--7" fluid><Alert color="warning">Aucune donnée de profil trouvée.</Alert></Container>;
  }

  // Nom et prénom peuvent venir de `user.first_name` ou `first_name`
  const firstName = userData.first_name || userData.nom;
  const lastName = userData.last_name || userData.prenom;

  return (
    <>
      <div className="header pb-8 pt-5 pt-lg-8 d-flex align-items-center" style={{ minHeight: '400px', backgroundSize: 'cover', backgroundPosition: 'center top' }}>
        <span className="mask bg-gradient-default opacity-8" />
        <Container className="d-flex align-items-center" fluid>
          <Row>
            <Col lg="7" md="10">
              <h1 className="display-2 text-white">Bonjour, {firstName} {lastName}</h1>
              <p className="text-white mt-0 mb-5">
                Ceci est votre page de profil. Vous pouvez consulter les informations de votre compte.
              </p>
            </Col>
          </Row>
        </Container>
      </div>
      <Container className="mt--7" fluid>
        <Row>
          <Col className="order-xl-1" xl="12">
            <Card className="bg-secondary shadow">
              <CardHeader className="bg-white border-0">
                <Row className="align-items-center">
                  <Col xs="8">
                    <h3 className="mb-0">Mon compte</h3>
                  </Col>
                  <Col className="text-right" xs="4">
                    <Button 
                      color="primary" 
                      tag={Link} 
                      to="/admin/profile-edit"
                      size="sm"
                    >
                      Modifier
                    </Button>
                  </Col>
                </Row>
              </CardHeader>
              <CardBody>
                <div className="pl-lg-4">
                  <h6 className="heading-small text-muted mb-4">Informations utilisateur</h6>
                  <div className="pl-lg-4">
                    <Row>
                      <ProfileField label="Prénom" value={userData?.first_name} />
                      <ProfileField label="Nom" value={userData?.last_name} />
                    </Row>
                    <Row>
                      <ProfileField label="Email" value={userData?.email} />
                      <ProfileField 
                        label="Statut du compte" 
                        value="Activé" 
                        isBadge 
                        color="success" 
                      />
                    </Row>
                    <Row>
                      <ProfileField 
                        label="Date de création" 
                        value={formatDate(userData.date_joined)} 
                      />
                      {userData?.last_login && (
                        <ProfileField 
                          label="Dernière connexion" 
                          value={formatDate(userData.last_login)} 
                        />
                      )}
                    </Row>
                    <Row>
                      <ProfileField label="Rôle" value={userData.role} />
                     
                    </Row>
                    
                  </div>
                </div>
              </CardBody>
            </Card>
          </Col>
        </Row>
      </Container>
    </>
  );
};

export default Profile;