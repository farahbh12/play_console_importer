import React, { useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import {
  Card,
  CardHeader,
  Table,
  Container,
  Row,
  Col,
  Spinner,
  Alert,
  Button,
} from 'reactstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCheckCircle, faFolder, faSync } from '@fortawesome/free-solid-svg-icons';

const DisplayGcsFiles = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState('');

  const fetchReportStatus = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('http://localhost:8000/display-gcs-files/', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.data.success) {
        setReports(response.data.data || []);
      } else {
        setError(response.data.error || 'An unknown error occurred.');
      }
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Failed to fetch report status.');
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchReportStatus();
  }, [fetchReportStatus]);

  const handleSync = async () => {
    setSyncing(true);
    setError('');
    setSyncMessage('');
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        'http://localhost:8000/trigger-gcs-sync/', 
        {}, 
        {
          headers: { 'Authorization': `Bearer ${token}` },
          timeout: 300000 // Timeout de 5 minutes
        }
      );
      setSyncMessage(response.data.message || 'Sync successful!');
      fetchReportStatus(); // Refresh the data after sync
    } catch (err) {
      setSyncMessage(err.response?.data?.error || 'Sync failed.');
    } finally {
      setSyncing(false);
    }
  };

  const getStatusIcon = (status) => {
    if (status === 'Ok') {
      return <FontAwesomeIcon icon={faCheckCircle} className="mr-2 text-success" />;
    } else if (status === 'n/a') {
      return <FontAwesomeIcon icon={faFolder} className="mr-2 text-muted" />;
    }
    return status;
  };

  return (
    <>
      <div className="header bg-gradient-info pb-8 pt-5 pt-md-8">
        <Container>
          <div className="header-body">
            <Row className="align-items-center">
              <Col>
                <h1 className="text-white mb-0">Source de données</h1>
              </Col>
              <Col className="text-right">
                <Button color="primary" onClick={handleSync} disabled={syncing} className="mb-3">
                  {syncing ? (
                    <>
                      <Spinner size="sm" /> Synchronisation...
                    </>
                  ) : (
                    <>
                      <FontAwesomeIcon icon={faSync} className="mr-2" /> Synchroniser les fichiers GCS
                    </>
                  )}
                </Button>
              </Col>
            </Row>
          </div>
        </Container>
      </div>
      <Container className="mt--7">
        {syncMessage && <Alert color={syncMessage.includes('failed') ? 'danger' : 'info'}>{syncMessage}</Alert>}
        {loading ? (
          <p>Chargement...</p>
        ) : error ? (
          <Alert color="danger">{error}</Alert>
        ) : (
          <Card className="shadow">
            <CardHeader className="border-0">
              <h3 className="mb-0">Statut des rapports</h3>
            </CardHeader>
            <Table className="align-items-center table-flush" responsive>
              <thead className="thead-light">
                <tr>
                  <th scope="col">Rapports</th>
                  <th scope="col">Statut</th>
                  <th scope="col">Dernières données disponibles</th>
                  <th scope="col">Détails</th>
                </tr>
              </thead>
              <tbody>
                {reports.map((report, index) => (
                  <tr key={index}>
                    <td>{report.name}</td>
                    <td>{getStatusIcon(report.status)} {report.status}</td>
                    <td>{report.last_modified}</td>
                    <td>{report.details}</td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Card>
        )}
      </Container>
    </>
  );
};

export default DisplayGcsFiles;