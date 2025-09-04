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
import { Link, useNavigate } from 'react-router-dom';

import { useAuth } from '../../contexts/AuthContext';
import employeeService from '../../services/employeeService';
import clientService from '../../services/clientService'; // Importer le service client
import authService from '../../services/auth';

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
  const navigate = useNavigate();

  // Récupération des données de l'utilisateur (employé, client owner, ou membre invité)
  useEffect(() => {
    const fetchUserData = async () => {
      if (!currentUser) {
        setError('Utilisateur non connecté. Veuillez vous connecter.');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError('');
        
        console.log('Current user in Profile:', currentUser);
        let data;
        const isInvitedUser = currentUser.role === 'MEMBRE_INVITE' || currentUser.role_client === 'MEMBRE_INVITE';
        const baseUserType = currentUser.user_type || (isInvitedUser ? 'client' : currentUser.role?.toLowerCase());

        // Essayer de récupérer les données en fonction du type d'utilisateur
        if (isInvitedUser || baseUserType === 'client') {
          try {
            const client = await clientService.getCurrent();
            console.log('Données client récupérées avec succès:', client);
            
            // Normaliser les données client
            data = {
              ...client,
              // Préserver le rôle original s'il existe, sinon utiliser le rôle du client
              role: client.role || currentUser.role,
              role_client: client.role_client || currentUser.role_client || (isInvitedUser ? 'MEMBRE_INVITE' : 'CLIENT'),
              first_name: client.first_name || client.prenom || currentUser.first_name || currentUser.prenom,
              last_name: client.last_name || client.nom || currentUser.last_name || currentUser.nom,
              email: client.email || currentUser.email,
              created_at: client.created_at || client.date_joined || currentUser.created_at,
              // Inclure tous les champs supplémentaires de currentUser qui ne sont pas déjà dans client
              ...Object.keys(currentUser).reduce((acc, key) => {
                if (key !== 'id' && !(key in client)) {
                  acc[key] = currentUser[key];
                }
                return acc;
              }, {})
            };
            
            // S'assurer que les champs de date sont correctement définis
            data.date_joined = data.created_at || data.date_joined;
            
            // Définir le type d'utilisateur pour le rendu conditionnel
            setUserType(isInvitedUser ? 'client_invite' : 'client');
            
          } catch (clientError) {
            console.warn('Impossible de charger le profil client, utilisation des données utilisateur locales:', clientError);
            
            // Utiliser les données utilisateur comme fallback
            data = {
              ...currentUser,
              first_name: currentUser.first_name || currentUser.prenom || currentUser.user?.first_name,
              last_name: currentUser.last_name || currentUser.nom || currentUser.user?.last_name,
              email: currentUser.email || currentUser.user?.email,
              created_at: currentUser.created_at || currentUser.date_joined,
              role_client: currentUser.role_client || (isInvitedUser ? 'MEMBRE_INVITE' : 'CLIENT')
            };
            
            setUserType(isInvitedUser ? 'client_invite' : 'client');
          }
        } 
        // Gestion des employés
        else if (baseUserType === 'employee' || currentUser.is_staff) {
          try {
            const employee = await employeeService.getCurrent();
            console.log('Données employé récupérées avec succès:', employee);
            
            data = {
              ...employee,
              role: employee.role_employe || 'Employé',
              first_name: employee.first_name || employee.prenom || currentUser.first_name,
              last_name: employee.last_name || employee.nom || currentUser.last_name,
              email: employee.email || currentUser.email,
              created_at: employee.created_at || employee.date_joined || currentUser.created_at,
              // Inclure les champs supplémentaires
              ...Object.keys(currentUser).reduce((acc, key) => {
                if (key !== 'id' && !(key in employee)) {
                  acc[key] = currentUser[key];
                }
                return acc;
              }, {})
            };
            
            setUserType('employee');
            
          } catch (employeeError) {
            console.warn('Impossible de charger le profil employé, utilisation des données utilisateur locales:', employeeError);
            
            // Fallback aux données utilisateur
            data = {
              ...currentUser,
              first_name: currentUser.first_name || currentUser.prenom,
              last_name: currentUser.last_name || currentUser.nom,
              email: currentUser.email,
              created_at: currentUser.created_at || currentUser.date_joined,
              role: currentUser.role_employe || 'Employé'
            };
            
            setUserType('employee');
          }
        }
        
        // Mettre à jour les données utilisateur
        if (data) {
          setUserData(data);
        } else {
          throw new Error('Aucune donnée utilisateur disponible');
        }

      } catch (error) {
        console.error(`Erreur lors du chargement du profil ${currentUser.user_type}:`, error);
        setError(error.message || `Impossible de charger le profil.`);
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, [currentUser]);
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

  // Nom/prénom/date peuvent venir de plusieurs champs possibles (Client ou User)
  const firstName = userData.first_name
    || userData.prenom
    || userData.firstName
    || userData.prenom_client
    || userData.user?.first_name
    || userData.user?.firstName;
  const lastName = userData.last_name
    || userData.nom
    || userData.lastName
    || userData.nom_client
    || userData.user?.last_name
    || userData.user?.lastName;
  const createdAt = userData.created_at
    || userData.date_joined
    || userData.created
    || userData.date_creation
    || userData.user?.date_joined;

  // Détecter de manière robuste si l'utilisateur est un membre invité
  const isInvited =
    userType === 'client_invite' ||
    (currentUser && (currentUser.role === 'MEMBRE_INVITE' || currentUser.role_client === 'MEMBRE_INVITE')) ||
    (userData && userData.role_client === 'MEMBRE_INVITE');

  const resolveUserId = () => {
    if (!currentUser && !userData) return null;
    // Le backend attend l'ID utilisateur dans l'URL (user_id)
    return (
      currentUser?.id ||
      currentUser?.user?.id ||
      userData?.user?.id ||
      userData?.user_id ||
      null
    );
  };

  const handleSelfDeactivate = async (e) => {
    if (e) { e.preventDefault(); e.stopPropagation(); }
    const userId = resolveUserId();
    if (!userId) {
      console.error('Impossible de déterminer l\'identifiant utilisateur pour la désactivation.');
      return;
    }
    try {
      await clientService.setStatus(userId, false);
    } catch (err) {
      console.error('Échec de la désactivation du compte:', err);
      // Même en cas d'erreur, on force la sortie pour éviter l'accès
    } finally {
      authService.logout();
      navigate('/auth/unauthorized', { replace: true });
    }
  };

  return (
    <>
      <div className="header pb-8 pt-5 pt-lg-8 d-flex align-items-center" style={{ minHeight: '400px', backgroundSize: 'cover', backgroundPosition: 'center top' }}>
        <span className="mask bg-gradient-info opacity-8" />
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
                    {isInvited ? (
                      <>
                        <Button
                          color="secondary"
                          size="sm"
                          disabled
                          onClick={(e) => { e.preventDefault(); e.stopPropagation(); }}
                          title="Les membres invités ne peuvent pas modifier leur profil."
                          className="mr-2"
                        >
                          Modifier
                        </Button>
                        <Button
                          color="danger"
                          size="sm"
                          onClick={handleSelfDeactivate}
                          title="Désactiver immédiatement votre compte invité et perdre l'accès."
                        >
                          Désactiver le compte
                        </Button>
                      </>
                    ) : (
                      <Button 
                        color="primary" 
                        tag={Link} 
                        to={userType === 'employee' ? '/admin/profile-edit' : '/client/profile-edit'}
                        size="sm"
                      >
                        Modifier
                      </Button>
                    )}
                  </Col>
                </Row>
              </CardHeader>
              <CardBody>
                <div className="pl-lg-4">
                  <h6 className="heading-small text-muted mb-4">Informations utilisateur</h6>
                  <div className="pl-lg-4">
                    <Row>
                      <ProfileField label="Prénom" value={firstName} />
                      <ProfileField label="Nom" value={lastName} />
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
                        value={formatDate(createdAt)} 
                      />
                      {userData?.last_login && (
                        <ProfileField 
                          label="Dernière connexion" 
                          value={formatDate(userData.last_login)} 
                        />
                      )}
                    </Row>
                    <Row>
                      {userType === 'employee' && (
                        <ProfileField label="Rôle" value={userData.role} />
                      )}
                      {userType === 'client_invite' && (
                        <ProfileField label="Rôle client" value={userData.role_client} />
                      )}
                      {userType === 'client' && userData.abonnement && (
                        <ProfileField label="Type d'abonnement" value={userData.abonnement.type} />
                      )}
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