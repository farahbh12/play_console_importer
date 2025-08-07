import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  CardHeader,
  CardBody,
  Container,
  Row,
  Col,
  Badge,
  Button
} from 'reactstrap';
import Header from '../../components/Headers/Header';
import authService from '../../services/auth';
import employeeService from '../../services/employeeService';

const AdminProfile = () => {
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        setLoading(true);
        const currentUser = authService.getCurrentUser();
        
        if (!currentUser) {
          navigate('/auth/login');
          return;
        }

        console.log('AdminProfile - Utilisateur connecté:', currentUser);

        // Essayer de récupérer le profil employé
        let profileData;
        try {
          profileData = await employeeService.getCurrent();
          console.log('AdminProfile - Profil employé récupéré:', profileData);
        } catch (empError) {
          console.log('AdminProfile - Erreur profil employé, utilisation des données de base');
          profileData = currentUser;
        }

        setUserData({
          ...currentUser,
          ...profileData
        });

      } catch (err) {
        console.error('AdminProfile - Erreur:', err);
        setError('Erreur lors du chargement du profil');
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [navigate]);

  const getUserRole = () => {
    if (!userData) return 'Utilisateur';
    
    if (userData.is_superuser || userData.role === 'administrateur' || userData.role === 'admin') {
      return 'Administrateur';
    }
    
    if (userData.role === 'gestionnaire' || userData.role === 'manager' || userData.role === 'employee') {
      return 'Gestionnaire';
    }
    
    return 'Employé';
  };

  const getFullName = () => {
    if (!userData) return 'Nom non disponible';
    
    // Essayer différentes combinaisons de champs
    if (userData.prenom && userData.nom) {
      return `${userData.prenom} ${userData.nom}`;
    }
    if (userData.first_name && userData.last_name) {
      return `${userData.first_name} ${userData.last_name}`;
    }
    if (userData.prenom && userData.last_name) {
      return `${userData.prenom} ${userData.last_name}`;
    }
    if (userData.first_name && userData.nom) {
      return `${userData.first_name} ${userData.nom}`;
    }
    
    return userData.email || 'Utilisateur';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Non défini';
    try {
      return new Date(dateString).toLocaleDateString('fr-FR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch {
      return 'Date invalide';
    }
  };

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ height: '50vh' }}>
        <div className="text-center">
          <div className="spinner-border text-primary" role="status">
            <span className="sr-only">Chargement...</span>
          </div>
          <p className="mt-2">Chargement du profil...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Container className="mt-7" fluid>
        <Row className="justify-content-center">
          <Col lg="8">
            <Card className="shadow">
              <CardBody className="text-center">
                <i className="ni ni-fat-remove text-danger" style={{ fontSize: '3rem' }}></i>
                <h3 className="text-danger mt-3">Erreur</h3>
                <p>{error}</p>
                <Button color="primary" onClick={() => window.location.reload()}>
                  Réessayer
                </Button>
              </CardBody>
            </Card>
          </Col>
        </Row>
      </Container>
    );
  }

  return (
    <>
      <Header />
      <Container className="mt--7" fluid>
        <Row>
          <Col className="order-xl-1" xl="8">
            <Card className="bg-secondary shadow">
              <CardHeader className="bg-white border-0">
                <Row className="align-items-center">
                  <Col xs="8">
                    <h3 className="mb-0">Profil Employé</h3>
                  </Col>
                  <Col className="text-right" xs="4">
                    <Button
                      color="primary"
                      onClick={() => navigate('/admin/profile-edit')}
                      size="sm"
                    >
                      Modifier
                    </Button>
                  </Col>
                </Row>
              </CardHeader>
              <CardBody>
                <div className="pl-lg-4">
                  <Row>
                    <Col lg="6">
                      <div className="form-group">
                        <label className="form-control-label">
                          Prénom
                        </label>
                        <div className="form-control-static">
                          {userData?.prenom || userData?.first_name || 'Non défini'}
                        </div>
                      </div>
                    </Col>
                    <Col lg="6">
                      <div className="form-group">
                        <label className="form-control-label">
                          Nom
                        </label>
                        <div className="form-control-static">
                          {userData?.nom || userData?.last_name || 'Non défini'}
                        </div>
                      </div>
                    </Col>
                  </Row>
                  <Row>
                    <Col lg="6">
                      <div className="form-group">
                        <label className="form-control-label">
                          Adresse e-mail
                        </label>
                        <div className="form-control-static">
                          {userData?.email || 'Non défini'}
                        </div>
                      </div>
                    </Col>
                    <Col lg="6">
                      <div className="form-group">
                        <label className="form-control-label">
                          Rôle
                        </label>
                        <div>
                          <Badge color="primary" pill className="mr-1">
                            {getUserRole()}
                          </Badge>
                        </div>
                      </div>
                    </Col>
                  </Row>
                  <Row>
                    <Col lg="6">
                      <div className="form-group">
                        <label className="form-control-label">
                          Statut
                        </label>
                        <div>
                          <Badge 
                            color={userData?.is_active ? 'success' : 'danger'} 
                            pill
                          >
                            {userData?.is_active ? 'Actif' : 'Inactif'}
                          </Badge>
                        </div>
                      </div>
                    </Col>
                    <Col lg="6">
                      <div className="form-group">
                        <label className="form-control-label">
                          ID Employé
                        </label>
                        <div className="form-control-static">
                          {userData?.employee_id || userData?.id || 'Non défini'}
                        </div>
                      </div>
                    </Col>
                  </Row>
                  {userData?.created_at && (
                    <Row>
                      <Col lg="6">
                        <div className="form-group">
                          <label className="form-control-label">
                            Date de création
                          </label>
                          <div className="form-control-static">
                            {formatDate(userData.created_at)}
                          </div>
                        </div>
                      </Col>
                      {userData?.updated_at && (
                        <Col lg="6">
                          <div className="form-group">
                            <label className="form-control-label">
                              Dernière mise à jour
                            </label>
                            <div className="form-control-static">
                              {formatDate(userData.updated_at)}
                            </div>
                          </div>
                        </Col>
                      )}
                    </Row>
                  )}
                </div>
              </CardBody>
            </Card>
          </Col>
          
          <Col className="order-xl-2 mb-5 mb-xl-0" xl="4">
            <Card className="card-profile shadow">
              <Row className="justify-content-center">
                <Col className="order-lg-2" lg="3">
                  <div className="card-profile-image">
                    <div className="avatar avatar-xl bg-gradient-primary rounded-circle text-white d-flex align-items-center justify-content-center">
                      <i className="ni ni-single-02" style={{ fontSize: '2rem' }}></i>
                    </div>
                  </div>
                </Col>
              </Row>
              <CardHeader className="text-center border-0 pt-8 pt-md-4 pb-0 pb-md-4">
                <div className="d-flex justify-content-between">
                  <Button
                    className="mr-4"
                    color="info"
                    size="sm"
                    onClick={() => navigate('/admin/index')}
                  >
                    Tableau de bord
                  </Button>
                  <Button
                    className="float-right"
                    color="default"
                    size="sm"
                    onClick={() => navigate('/admin/profile-edit')}
                  >
                    Modifier
                  </Button>
                </div>
              </CardHeader>
              <CardBody className="pt-0 pt-md-4">
                <div className="text-center">
                  <h3>
                    {getFullName()}
                  </h3>
                  <div className="h5 font-weight-300">
                    <i className="ni location_pin mr-2" />
                    {getUserRole()}
                  </div>
                  <div className="h5 mt-4">
                    <i className="ni business_briefcase-24 mr-2" />
                    Employé depuis {formatDate(userData?.created_at)}
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

export default AdminProfile;
