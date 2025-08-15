import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { verifyInvitation } from '../../services/teamService';
import { Card, CardBody, Container, Row, Col, Spinner } from 'reactstrap';

const GuestLogin = () => {
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();
  const { loginWithTokens } = useAuth();

  useEffect(() => {
    const token = new URLSearchParams(location.search).get('token');

    if (!token) {
      setError('No invitation token found. Please use the link from your email.');
      setLoading(false);
      return;
    }

    const processInvitation = async () => {
      try {
        const response = await verifyInvitation(token);
        
        // The backend creates the user and returns tokens.
        // Now, log the user in on the frontend. This function will handle setting the session.
        await loginWithTokens(response.access, response.refresh, response.user);

        // Now that the session is guaranteed to be set, we can safely navigate.
        // The invited member is redirected directly to the destination page.
        navigate('/client/gcs-connector', { replace: true });

      } catch (err) {
        const errorMessage = err.response?.data?.error || 'An unknown error occurred. The invitation may be invalid or expired.';
        setError(errorMessage);
        setLoading(false);
      }
    };

    processInvitation();
  }, [location, navigate, loginWithTokens]);

  return (
    <Container className="mt--7">
      <Row className="justify-content-center">
        <Col lg="5" md="7">
          <Card className="bg-secondary shadow border-0">
            <CardBody className="px-lg-5 py-lg-5 text-center">
              {loading && (
                <div>
                  <Spinner color="primary" />
                  <p className="mt-3">Verifying your invitation...</p>
                </div>
              )}
              {error && (
                <div>
                  <p className="text-danger">{error}</p>
                  <p>Please contact the person who invited you for assistance.</p>
                </div>
              )}
            </CardBody>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default GuestLogin;
