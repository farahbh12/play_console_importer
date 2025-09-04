import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button, Card, CardBody, FormGroup, Form, Input, InputGroup, InputGroupText, Container, Col, Row, FormFeedback, Alert } from 'reactstrap';
// toast est importé automatiquement par react-toastify
import authService from '../../services/authService';

const ResetPassword = () => {
  const { uid, token } = useParams();
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [password2, setPassword2] = useState('');
  const [loading, setLoading] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({ password: '', password2: '' });
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFieldErrors({ password: '', password2: '' });
    setErrorMsg('');
    setSuccessMsg('');
    let hasClientErr = false;
    const fe = { password: '', password2: '' };
    if (!password) { fe.password = 'Mot de passe requis.'; hasClientErr = true; }
    if (!password2) { fe.password2 = 'Confirmation requise.'; hasClientErr = true; }
    if (password && password.length < 8) { fe.password = 'Minimum 8 caractères.'; hasClientErr = true; }
    if (password && password2 && password !== password2) { fe.password2 = 'Les mots de passe ne correspondent pas.'; hasClientErr = true; }
    if (hasClientErr) { setFieldErrors(fe); return; }
    setLoading(true);
    try {
      await authService.confirmPasswordReset(uid, token, password, password2);
      setSuccessMsg('Votre mot de passe a été réinitialisé avec succès ! Vous pouvez maintenant vous connecter.');
      navigate('/auth/login');
    } catch (error) {
      const backend = error.response?.data;
      if (backend?.password) fe.password = Array.isArray(backend.password) ? backend.password[0] : String(backend.password);
      if (backend?.password2) fe.password2 = Array.isArray(backend.password2) ? backend.password2[0] : String(backend.password2);
      setFieldErrors({ ...fe });
      const errorMessage = backend?.detail || 'Le lien est invalide ou a expiré.';
      setErrorMsg(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container className="mt--7">
      <Row className="justify-content-center">
        <Col lg="5" md="7">
          <Card className="bg-secondary shadow border-0">
            <CardBody className="px-lg-5 py-lg-5">
              <div className="text-center text-muted mb-4">
                <small>Réinitialiser votre mot de passe</small>
              </div>
              {errorMsg && <Alert color="danger">{errorMsg}</Alert>}
              {successMsg && <Alert color="success">{successMsg}</Alert>}
              <Form role="form" onSubmit={handleSubmit}>
                <FormGroup>
                  <InputGroup className="input-group-merge input-group-alternative">
                    <InputGroupText>
                      <i className="ni ni-lock-circle-open" />
                    </InputGroupText>
                    <Input
                      placeholder="Nouveau mot de passe"
                      type="password"
                      autoComplete="new-password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      invalid={!!fieldErrors.password}
                    />
                    {fieldErrors.password ? <FormFeedback className="d-block small mb-0">{fieldErrors.password}</FormFeedback> : null}
                  </InputGroup>
                </FormGroup>
                <FormGroup>
                  <InputGroup className="input-group-merge input-group-alternative">
                    <InputGroupText>
                      <i className="ni ni-lock-circle-open" />
                    </InputGroupText>
                    <Input
                      placeholder="Confirmer le mot de passe"
                      type="password"
                      autoComplete="new-password"
                      value={password2}
                      onChange={(e) => setPassword2(e.target.value)}
                      required
                      invalid={!!fieldErrors.password2}
                    />
                    {fieldErrors.password2 ? <FormFeedback className="d-block small mb-0">{fieldErrors.password2}</FormFeedback> : null}
                  </InputGroup>
                </FormGroup>
                <div className="text-center">
                  <Button
                    className="my-4"
                    color="primary"
                    type="submit"
                    disabled={loading}
                  >
                    {loading ? 'Traitement en cours...' : 'Réinitialiser le mot de passe'}
                  </Button>
                </div>
              </Form>
            </CardBody>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default ResetPassword;
