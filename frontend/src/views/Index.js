/*!

=========================================================
* Argon Dashboard React - v1.2.4
=========================================================

* Product Page: https://www.creative-tim.com/product/argon-dashboard-react
* Copyright 2024 Creative Tim (https://www.creative-tim.com)
* Licensed under MIT (https://github.com/creativetimofficial/argon-dashboard-react/blob/master/LICENSE.md)

* Coded by Creative Tim

=========================================================

* The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

*/
import React, { useState, useEffect, useContext } from "react";

import { 
  Card, 
  CardBody, 
  Container, 
  Row, 
  Col, 
  Progress, 
} from "reactstrap";
import { AuthContext } from "../contexts/AuthContext";
import Header from "../components/Headers/Header";

// Import des icônes
import { 
  faUser, 
  faCreditCard, 
  faChartBar, 
 
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

function Index() {
  const { currentUser } = useContext(AuthContext);

  
  // État pour les statistiques du tableau de bord
  const [stats, setStats] = useState({
    totalClients: 0,
    activeSubscriptions: 0,
    storageUsed: 0,
    totalStorage: 100, // 100 Go par défaut
  });
  
  // Calcul du pourcentage de stockage utilisé
  const storagePercentage = (stats.storageUsed / stats.totalStorage) * 100;
  
  // Vérifier si l'utilisateur est admin
  const isAdmin = currentUser?.user_type === 'employee' && 
                 (currentUser?.role === 'Administrateur' || currentUser?.is_superuser);
  
  // Charger les données du tableau de bord
  useEffect(() => {
    // Simuler le chargement des données
    // Dans une application réelle, vous feriez un appel API ici
    const loadDashboardData = async () => {
      try {
        // Simulation de données
        setTimeout(() => {
          setStats({
            totalClients: 42,
            activeSubscriptions: 36,
            storageUsed: 45.7,
            totalStorage: 100
          });
        }, 1000);
      } catch (error) {
        console.error("Erreur lors du chargement des statistiques:", error);
      }
    };

    loadDashboardData();
  }, []);

  // Rendu du tableau de bord
  const renderDashboard = () => (
    <Container className="mt--7" fluid>
      <Row className="mt-5">
        {/* Carte Nombre total de clients */}
        <Col xl="4" md="6">
          <Card className="card-stats mb-4 mb-xl-0">
            <CardBody>
              <Row>
                <div className="col">
                  <h5 className="card-title text-uppercase text-muted mb-0">
                    {isAdmin ? 'Total Clients' : 'Mes Clients'}
                  </h5>
                  <span className="h2 font-weight-bold mb-0">{stats.totalClients}</span>
                </div>
                <Col className="col-auto">
                  <div className="icon icon-shape bg-gradient-red text-white rounded-circle shadow">
                    <FontAwesomeIcon icon={faUser} />
                  </div>
                </Col>
              </Row>
              <p className="mt-3 mb-0 text-sm">
                <span className="text-nowrap">Mis à jour à l'instant</span>
              </p>
            </CardBody>
          </Card>
        </Col>

        {/* Carte Abonnements actifs */}
        <Col xl="4" md="6">
          <Card className="card-stats mb-4 mb-xl-0">
            <CardBody>
              <Row>
                <div className="col">
                  <h5 className="card-title text-uppercase text-muted mb-0">
                    Abonnements actifs
                  </h5>
                  <span className="h2 font-weight-bold mb-0">{stats.activeSubscriptions}</span>
                </div>
                <Col className="col-auto">
                  <div className="icon icon-shape bg-gradient-orange text-white rounded-circle shadow">
                    <FontAwesomeIcon icon={faCreditCard} />
                  </div>
                </Col>
              </Row>
              <p className="mt-3 mb-0 text-sm">
                <span className="text-nowrap">Sur {stats.totalClients} clients</span>
              </p>
            </CardBody>
          </Card>
        </Col>

        {/* Carte Stockage utilisé */}
        <Col xl="4" md="6">
          <Card className="card-stats mb-4 mb-xl-0">
            <CardBody>
              <Row>
                <div className="col">
                  <h5 className="card-title text-uppercase text-muted mb-0">Stockage utilisé</h5>
                  <span className="h2 font-weight-bold mb-0">
                    {stats.storageUsed} <small>Go</small>
                  </span>
                </div>
                <Col className="col-auto">
                  <div className="icon icon-shape bg-gradient-info text-white rounded-circle shadow">
                    <FontAwesomeIcon icon={faChartBar} />
                  </div>
                </Col>
              </Row>
              <p className="mt-3 mb-0 text-sm">
                <span className="text-nowrap">{storagePercentage.toFixed(1)}% du total</span>
              </p>
              <Progress
                className="mt-2"
                color="info"
                value={storagePercentage}
                max="100"
              />
            </CardBody>
          </Card>
        </Col>
      </Row>
    </Container>
  );

  // Rendu du contenu principal
  const renderContent = () => {
    // Afficher un indicateur de chargement si nécessaire
    if (stats.totalClients === 0) {
      return (
        <div className="text-center py-5">
          <div className="spinner-border text-primary" role="status">
            <span className="sr-only">Chargement...</span>
          </div>
          <p className="mt-2">Chargement des données...</p>
        </div>
      );
    }

    // Rendu du tableau de bord selon le rôle
    return renderDashboard();
  };

  return (
    <>
      <Header />
      {/* Page content */}
      {renderContent()}
    </>
  );
};

export default Index;
