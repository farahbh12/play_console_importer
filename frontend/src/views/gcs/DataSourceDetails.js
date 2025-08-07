import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
  Container,
  Row,
  Col,
  Spinner,
  Alert,
  Card,
  CardBody,
  CardHeader,
  Button
} from 'reactstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
    faInfoCircle, faFileAlt, faDatabase
} from '@fortawesome/free-solid-svg-icons';
import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

const DataSourceDetails = () => {
  const [dataSource, setDataSource] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');

  const fetchDataSourceDetails = useCallback(async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get('http://localhost:8000/data-source-details/', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.data.success) {
        setDataSource(response.data.data);
      } else {
        setError(response.data.error || 'Failed to fetch data source details.');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error connecting to the server.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDataSourceDetails();
  }, [fetchDataSourceDetails]);

  const triggerSync = async () => {
    try {
      setError(null);
      setSuccessMessage('');
      const token = localStorage.getItem('token');
      const response = await axios.post('http://localhost:8000/trigger-gcs-sync/', {}, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      
      if (response.data.success) {
        setSuccessMessage('Synchronization started successfully!');
        // Refresh data after a short delay
        setTimeout(fetchDataSourceDetails, 2000);
      } else {
        setError(response.data.error || 'Failed to start synchronization.');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error connecting to the server.');
    }
  };

  const getChartData = (status) => {
    const statusConfig = {
      completed: { label: 'Terminée', color: '#2dce89', data: [100, 0] },
      in_progress: { label: 'En cours', color: '#5e72e4', data: [50, 50] },
      failed: { label: 'Échouée', color: '#f5365c', data: [100, 0] },
      pending: { label: 'En attente', color: '#adb5bd', data: [0, 100] },
      default: { label: 'Inconnu', color: '#8898aa', data: [0, 100] },
    };
    const config = statusConfig[status] || statusConfig.default;

    return {
      labels: [config.label, ''],
      datasets: [{
        data: config.data,
        backgroundColor: [config.color, '#e9ecef'],
        borderColor: '#fff',
        borderWidth: 2,
        circumference: 180, // Semi-circle
        rotation: -90,      // Start from the top
      }],
    };
  };

  const chartOptions = {
    plugins: { legend: { display: false }, tooltip: { enabled: false } },
    responsive: true,
    maintainAspectRatio: false,
    cutout: '80%',
  };

  const renderContent = () => {
    if (loading) {
      return <div className="text-center my-5"><Spinner /></div>;
    }

    if (dataSource?.status === 'not_found' || !dataSource) {
      return (
        <Alert color="info" className="text-center">
          <FontAwesomeIcon icon={faInfoCircle} size="2x" className="mb-2" />
          <h4 className="alert-heading">Aucune Source de Données</h4>
          <p>Aucune source de données n'a été trouvée. Lancez une synchronisation pour en créer une.</p>
        </Alert>
      );
    }

    const chartData = getChartData(dataSource.status);
    const statusLabel = chartData.labels[0];

    return (
        <Card className="shadow-sm">
            <CardHeader className="bg-transparent">
                <h3 className="mb-0">Aperçu de la Synchronisation</h3>
            </CardHeader>
            <CardBody>
                <Row>
                    <Col lg="6" className="d-flex flex-column justify-content-center align-items-center">
                        <div style={{ position: 'relative', width: '200px', height: '100px' }}>
                            <Doughnut data={chartData} options={chartOptions} />
                            <div className="text-center" style={{ position: 'absolute', top: '70%', left: '50%', transform: 'translate(-50%, -50%)' }}>
                                <h3 className="mb-0">{statusLabel}</h3>
                            </div>
                        </div>
                        <p className="text-muted mt-3">
                            Dernière MàJ: {dataSource.last_sync ? new Date(dataSource.last_sync).toLocaleString('fr-FR') : 'Jamais'}
                        </p>
                    </Col>
                    <Col lg="6">
                        <div className="d-flex align-items-center my-3">
                            <FontAwesomeIcon icon={faFileAlt} size="2x" className="text-warning mr-3" />
                            <div>
                                <span className="d-block h4">{dataSource.files_processed}</span>
                                <span className="text-muted">Fichiers Traités</span>
                            </div>
                        </div>
                        <div className="d-flex align-items-center my-3">
                            <FontAwesomeIcon icon={faDatabase} size="2x" className="text-success mr-3" />
                            <div>
                                <span className="d-block h4">{dataSource.records_inserted.toLocaleString('fr-FR')}</span>
                                <span className="text-muted">Enregistrements</span>
                            </div>
                        </div>
                    </Col>
                </Row>
               
            </CardBody>
        </Card>
    );
  };

  return (
    <>
      <div className="header bg-gradient-info pb-8 pt-5 pt-md-8">
        <Container fluid>
          <div className="header-body">
            <Row className="align-items-center">
              <Col>
                <h2 className="text-white mb-0">Source de Données GCS</h2>
                <p className="text-white mt-2 mb-0">Consultez l'état de votre source de données et lancez de nouvelles synchronisations.</p>
              </Col>
              <Col className="text-right">
                
              </Col>
            </Row>
          </div>
        </Container>
      </div>
      <Container className="mt--7" fluid>
        {error && <Alert color="danger" className="mb-3">{error}</Alert>}
        {successMessage && <Alert color="success" className="mb-3">{successMessage}</Alert>}
        <Button color="primary" onClick={triggerSync} className="mb-3">Lancer la synchronisation</Button>
        {renderContent()}
      </Container>
    </>
  );
};

export default DataSourceDetails;