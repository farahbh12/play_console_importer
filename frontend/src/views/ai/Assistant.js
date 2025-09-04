import React, { useState, useEffect } from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  Container,
  Row,
  Col,
  FormGroup,
  Input,
  Label,
  Button,
  Spinner,
  Alert,
  Badge,
  Progress,
  CardTitle,
  CardText,
  ListGroup,
  ListGroupItem
} from 'reactstrap';
import { toast } from 'react-toastify';
import api from '../../services/api';

const GooglePlayAssistant = () => {
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [packageName, setPackageName] = useState('');
  const [packages, setPackages] = useState([]);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [error, setError] = useState('');

  // Set default date range (last 30 days)
  useEffect(() => {
    const end = new Date();
    const start = new Date();
    start.setDate(end.getDate() - 30);
    
    setStartDate(start.toISOString().split('T')[0]);
    setEndDate(end.toISOString().split('T')[0]);
  }, []);

  // Fetch available packages
  useEffect(() => {
    const fetchPackages = async () => {
      try {
        const response = await api.get('/insights/packages');
        if (response.data.success && response.data.packages.length > 0) {
          setPackages(response.data.packages);
          setPackageName(response.data.packages[0]);
        }
      } catch (err) {
        console.error('Error fetching packages:', err);
        toast.error('Failed to load packages');
      }
    };
    fetchPackages();
  }, []);

  const analyzeData = async () => {
    if (!packageName) {
      setError('Please select a package');
      return;
    }

    if (!startDate || !endDate) {
      setError('Please select both start and end dates');
      return;
    }

    if (new Date(startDate) > new Date(endDate)) {
      setError('Start date must be before end date');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const params = {
        package_name: packageName,
        start: startDate,
        end: endDate,
      };

      const response = await api.get('/insights/ai_analysis', { params });
      
      if (response.data.success) {
        setAnalysis(response.data.analysis);
      } else {
        setError(response.data.error || 'Failed to analyze data');
      }
    } catch (err) {
      console.error('Analysis error:', err);
      setError('An error occurred while analyzing the data');
    } finally {
      setLoading(false);
    }
  };

  const renderMetricCard = (title, value, delta, isPositive = true, format = 'number') => {
    // Handle null/undefined values
    if (value === null || value === undefined) {
      value = 0;
    }

    let formattedValue = 'N/A';
    
    try {
      if (format === 'percent') {
        formattedValue = `${(parseFloat(value) * 100).toFixed(1)}%`;
      } else if (format === 'rating') {
        formattedValue = parseFloat(value).toFixed(1);
      } else {
        formattedValue = new Intl.NumberFormat().format(Number(value));
      }
    } catch (e) {
      console.error('Error formatting value:', { value, format, error: e });
      formattedValue = 'N/A';
    }

    return (
      <Card className="mb-4">
        <CardBody>
          <div className="d-flex justify-content-between align-items-center">
            <div>
              <h6 className="text-uppercase text-muted mb-0">{title}</h6>
              <h2 className="mb-0">{formattedValue}</h2>
            </div>
            {delta !== undefined && delta !== null && !isNaN(delta) && (
              <Badge color={isPositive ? 'success' : 'danger'} className="p-2">
                {delta > 0 ? '↑' : '↓'} {Math.abs(delta).toFixed(1)}%
              </Badge>
            )}
          </div>
        </CardBody>
      </Card>
    );
  };

  return (
    <>
      <div className="header bg-gradient-info pb-8 pt-5 pt-md-8">
        <Container fluid>
          <div className="header-body">
            <Row className="align-items-center py-4">
              <Col lg="6" xs="7">
                <h6 className="h2 text-white d-inline-block mb-0">Assistant d'Analyse</h6>
              </Col>
            </Row>
          </div>
        </Container>
      </div>
      <Container className="mt--7" fluid>
        <Card className="shadow">
          <CardHeader className="border-0">
            <Row className="align-items-center">
              <div className="col">
                <h3 className="mb-0">Analyse des Performances</h3>
              </div>
            </Row>
          </CardHeader>
          <CardBody>
            <Row>
              <Col md="4">
                <FormGroup>
                  <Label className="form-control-label" for="packageSelect">
                    Nom du Package
                  </Label>
                  <div className="input-group input-group-merge input-group-alternative">
                    <div className="input-group-prepend">
                      <span className="input-group-text">
                        <i className="ni ni-app" />
                      </span>
                    </div>
                    <Input
                      className="form-control-alternative"
                      type="select"
                      id="packageSelect"
                      value={packageName}
                      onChange={(e) => setPackageName(e.target.value)}
                      disabled={loading}
                    >
                      <option value="">Sélectionner un package</option>
                      {packages.map((pkg) => (
                        <option key={pkg} value={pkg}>
                          {pkg}
                        </option>
                      ))}
                    </Input>
                  </div>
                </FormGroup>
              </Col>
              <Col md="3">
                <FormGroup>
                  <Label for="startDate">Start Date</Label>
                  <Input
                    type="date"
                    id="startDate"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    disabled={loading}
                  />
                </FormGroup>
              </Col>
              <Col md="3">
                <FormGroup>
                  <Label for="endDate">End Date</Label>
                  <Input
                    type="date"
                    id="endDate"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    disabled={loading}
                  />
                </FormGroup>
              </Col>
              <Col md="2" className="d-flex align-items-end">
                <Button
                  color="primary"
                  onClick={analyzeData}
                  disabled={loading}
                  className="w-100"
                >
                  {loading ? <Spinner size="sm" /> : 'Analyze'}
                </Button>
              </Col>
            </Row>

            {error && <Alert color="danger">{error}</Alert>}

            {loading && (
              <div className="text-center py-4">
                <Spinner color="primary" />
                <p className="mt-2 mb-0">Analyzing your app's performance...</p>
              </div>
            )}

            {analysis && (
              <div className="mt-4">
                <h4 className="mb-4">Key Metrics</h4>
                <Row>
                  <Col md="3">
                    {renderMetricCard(
                      'Total Installs', 
                      analysis.key_metrics?.installs?.total_installs || 0,
                      null,
                      true,
                      'number'
                    )}
                  </Col>
                  <Col md="3">
                    {renderMetricCard(
                      'Avg. Rating', 
                      analysis.key_metrics?.ratings?.avg_rating || 0,
                      analysis.key_metrics?.ratings?.avg_rating_delta,
                      (analysis.key_metrics?.ratings?.avg_rating_delta || 0) >= 0,
                      'rating'
                    )}
                  </Col>
                  <Col md="3">
                    {renderMetricCard(
                      'Crash Rate', 
                      analysis.key_metrics?.crashes?.avg_daily_crashes || 0,
                      null,
                      (analysis.key_metrics?.crashes?.avg_daily_crashes || 0) < 0.05,
                      'percent'
                    )}
                  </Col>
                  <Col md="3">
                    {renderMetricCard(
                      'Total Crashes', 
                      analysis.key_metrics?.crashes?.total_crashes || 0,
                      null,
                      (analysis.key_metrics?.crashes?.total_crashes || 0) === 0,
                      'number'
                    )}
                  </Col>
                </Row>

                {analysis.detailed_description && (
                  <Card className="mt-4">
                    <CardBody>
                      <h5 className="mb-3">Analyse Détaillée</h5>
                      <p className="mb-0">{analysis.detailed_description}</p>
                    </CardBody>
                  </Card>
                )}

                {analysis.recommendations?.length > 0 && (
                  <>
                    <h4 className="mb-4 mt-5">Recommendations</h4>
                    <ListGroup>
                      {analysis.recommendations.map((rec, idx) => (
                        <ListGroupItem key={idx}>
                          <div className="d-flex align-items-center">
                            <span>{rec}</span>
                          </div>
                        </ListGroupItem>
                      ))}
                    </ListGroup>
                  </>
                )}
              </div>
            )}
          </CardBody>
        </Card>
      </Container>
    </>
  );
};

export default GooglePlayAssistant;
