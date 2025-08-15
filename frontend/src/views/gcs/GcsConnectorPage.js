import React from 'react';
import { Container, Row, Col } from 'reactstrap';
import ConnectorCard from '../../components/ConnectorCard';

const GcsConnectorPage = () => {

  const handleOpen = () => {
    const lookerStudioUrl = 'https://lookerstudio.google.com/datasources/create?connectorId=AKfycbwsbUsPC0zgnBDbCfiYEszzBLndZz8MhVc8jMFuimo';
    window.open(lookerStudioUrl, '_blank', 'noopener,noreferrer');
  };

  const handleRevoke = () => {
    alert('Révocation de l\'accès...');
  };

  return (
    <>
      <div className="header bg-gradient-info pb-8 pt-5 pt-md-8">
        <Container>
          <div className="header-body">
            <h2 className="text-white">Connecteurs de Données</h2>
            <p className="text-white mt-2 mb-0">Gérez les connexions à vos plateformes de données comme Looker Studio.</p>
          </div>
        </Container>
      </div>
      <Container className="mt--7">
        <Row className="justify-content-start" style={{ marginTop: '6rem' }}>
          <Col lg="8" className="text-left">
            <h3 className="mb-2">Destinations Looker Studio</h3>
            <p className="text-muted mb-0">
              Connecteurs pour l’intelligence d’affaires et la visualisation de données.
            </p>
          </Col>
        </Row>
        <Row className="justify-content-start" style={{ marginTop: '1rem' }}>
          <Col lg="6">
            <ConnectorCard
              title="Looker Studio Connector"
              subtitle="Google Data Platform"
              isActive={true} // Statut à dynamiser plus tard
              onOpen={handleOpen}
              onRevoke={handleRevoke}
              logoSrc="https://www.gstatic.com/analytics-suite/header/suite/v2/ic_data_studio.svg"
            />
          </Col>
        </Row>
      </Container>
    </>
  );
};

export default GcsConnectorPage;
