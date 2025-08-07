import React, { useState } from 'react';
import { Button, Card, CardBody, FormGroup, Form, Input, InputGroup, InputGroupText, Container, Col, Row } from 'reactstrap';
import { toast } from 'react-toastify';
import authService from '../../services/authService';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await authService.requestPasswordReset(email);
      toast.success('Un email de réinitialisation a été envoyé. Veuillez vérifier votre boîte de réception.');
    } catch (error) {
      toast.error(error.detail || 'Une erreur est survenue.');
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
                <small>Réinitialiser le mot de passe</small>
              </div>
              <Form role="form" onSubmit={handleSubmit}>
                <FormGroup>
                  <InputGroup className="input-group-merge input-group-alternative">
                    <InputGroupText>
                      <i className="ni ni-email-83" />
                    </InputGroupText>
                    <Input
                      placeholder="Email"
                      type="email"
                      autoComplete="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                    />
                  </InputGroup>
                </FormGroup>
                <div className="text-center">
                  <Button
                    className="my-4"
                    color="primary"
                    type="submit"
                    disabled={loading}
                  >
                    {loading ? 'Envoi en cours...' : 'Réinitialiser le mot de passe'}
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

export default ForgotPassword;
