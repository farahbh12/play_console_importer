import React, { useState, useEffect, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import teamService from '../../services/teamService';
import {
  Container, Row, Col, Card, CardBody, Form, FormGroup,
  Input, Button, Spinner, Alert, FormFeedback
} from 'reactstrap';

const AcceptInvitation = () => {
  const { loginWithTokens } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  
  const [invitationData, setInvitationData] = useState(null);
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [fieldErrors, setFieldErrors] = useState({ password: '', confirmPassword: '' });

  const getTokenFromURL = useCallback(() => {
    // Try query param first: ?token=...
    const params = new URLSearchParams(location.search);
    const queryToken = params.get('token');
    if (queryToken) return queryToken;
    // Fallback to last path segment: /.../<token>
    const parts = location.pathname.split('/').filter(Boolean);
    return parts[parts.length - 1] || null;
  }, [location.search, location.pathname]);

  useEffect(() => {
    const token = getTokenFromURL();
    if (!token) {
      setError('Aucun jeton d\'invitation fourni.');
      setLoading(false);
      return;
    }

    teamService.checkInvitation(token)
      .then(data => {
        setInvitationData(data);
        setLoading(false);
      })
      .catch(err => {
        const errorMessage = err.response?.data?.error || 'Le lien d\'invitation est invalide ou a expiré.';
        setError(errorMessage);
        setLoading(false);
      });
  }, [getTokenFromURL]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setFieldErrors({ password: '', confirmPassword: '' });

    let hasClientErr = false;
    const fe = { password: '', confirmPassword: '' };
    if (!password) { fe.password = 'Mot de passe requis.'; hasClientErr = true; }
    if (!confirmPassword) { fe.confirmPassword = 'Confirmation requise.'; hasClientErr = true; }
    if (password && password.length < 8) { fe.password = 'Minimum 8 caractères.'; hasClientErr = true; }
    if (password && confirmPassword && password !== confirmPassword) { fe.confirmPassword = 'Les mots de passe ne correspondent pas.'; hasClientErr = true; }
    if (hasClientErr) { setFieldErrors(fe); return; }

    const token = getTokenFromURL();
    setLoading(true);

    try {
      const response = await teamService.verifyInvitation(token, password);
      setSuccess('Votre compte a été activé avec succès ! Vous allez être redirigé vers la page de gestion d\'équipe.');
      setTimeout(async () => {
        await loginWithTokens(response.access, response.refresh, response.user);
        const role = response?.user?.role;
        const dest = role === 'MEMBRE_INVITE' ? '/client/source' : '/client/manage-team';
        navigate(dest, { replace: true });
      }, 3000);
    } catch (err) {
      const backend = err.response?.data;
      const fe2 = { password: '', confirmPassword: '' };
      if (backend?.password) fe2.password = Array.isArray(backend.password) ? backend.password[0] : String(backend.password);
      if (backend?.password_confirm) fe2.confirmPassword = Array.isArray(backend.password_confirm) ? backend.password_confirm[0] : String(backend.password_confirm);
      setFieldErrors(fe2);
      const errorMessage = backend?.error || backend?.detail || 'Une erreur est survenue lors de l\'activation du compte.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !invitationData) {
    return (
      <Container className="mt-5 text-center">
        <Spinner /><p>Vérification de l'invitation...</p>
      </Container>
    );
  }

  return (
    <Container className="mt-5">
      <Row className="justify-content-center">
        <Col lg="5" md="7">
          <Card className="bg-secondary shadow border-0">
            <CardBody className="px-lg-5 py-lg-5">
              <div className="text-center text-muted mb-4">
                <h3>Activer votre compte</h3>
              </div>
              
              {error && <Alert color="danger">{error}</Alert>}
              {success && <Alert color="success">{success}</Alert>}

              {invitationData && !success && (
                <>
                  <div className="text-center mb-4">
                    
                    <p>Veuillez définir un mot de passe pour votre compte </p>
                  </div>
                  
                  <Form role="form" onSubmit={handleSubmit}>
                    <FormGroup>
                      <Input placeholder="Nouveau mot de passe" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength="8" invalid={!!fieldErrors.password} />
                      {fieldErrors.password ? <FormFeedback className="d-block small mb-0">{fieldErrors.password}</FormFeedback> : null}
                    </FormGroup>
                    <FormGroup>
                      <Input placeholder="Confirmer le mot de passe" type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required invalid={!!fieldErrors.confirmPassword} />
                      {fieldErrors.confirmPassword ? <FormFeedback className="d-block small mb-0">{fieldErrors.confirmPassword}</FormFeedback> : null}
                    </FormGroup>
                    <div className="text-center">
                      <Button className="my-4" color="primary" type="submit" disabled={loading}>
                        {loading ? <Spinner size="sm" /> : 'Activer mon compte'}
                      </Button>
                    </div>
                  </Form>
                </>
              )}
            </CardBody>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default AcceptInvitation;