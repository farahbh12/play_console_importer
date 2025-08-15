import React, { useState, useEffect } from 'react';
import {
  Button,
  Card,
  CardHeader,
  CardBody,
  Container,
  Row,
  Col,
  Table,
  Modal,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Form,
  FormGroup,
  Label,
  Input,
  Alert
} from 'reactstrap';
import teamService from '../../services/teamService';
import clientService from '../../services/clientService';

const ManageTeam = () => {
  const [teamMembers, setTeamMembers] = useState([]);
  const [actionLoadingId, setActionLoadingId] = useState(null);

  const [modal, setModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');

  const [inviteError, setInviteError] = useState('');
  const [inviteSuccess, setInviteSuccess] = useState('');

  const toggleModal = () => setModal(!modal);

  const fetchMembers = async () => {
    try {
      // Call the correct service (returns data directly)
      const membersData = await teamService.getTeamMembers();
      console.log('API Response Data:', membersData); // Debugging line
      const formattedMembers = membersData.map(m => {
        if (m.user && m.role_client) { // This is an active member or owner (Client model)
          return {
            id: m.id,
            userId: m.user?.id,
            name: `${m.user.first_name || ''} ${m.user.last_name || ''}`.trim() || m.user.email,
            email: m.user.email,
            status: m.role_client === 'Owner' ? 'Owner' : (m.status || 'Active'),
            role: m.role_client
          };
        } else { // This is a pending invitation (Invitation model)
          return {
            id: m.id,
            userId: null,
            name: `${m.first_name || ''} ${m.last_name || ''}`.trim() || m.email,
            email: m.email,
            status: 'Pending',
            role: 'MEMBRE_INVITE'
          };
        }
      });
      setTeamMembers(formattedMembers);
    } catch (err) {
      console.error('Failed to fetch team members:', err);
    } finally {

    }
  };

  useEffect(() => {
    fetchMembers();
  }, []);

  const handleToggleActive = async (member) => {
    // Le backend attend l'ID UTILISATEUR (user_id) dans l'URL
    if (!member.userId) return; // Can't toggle for pending invitations
    try {
      setActionLoadingId(member.userId);
      const isActive = member.status === 'Active';
      await clientService.setStatus(member.userId, !isActive);
    } catch (err) {
      console.error('Failed to toggle status:', err);
    } finally {
      setActionLoadingId(null);
      fetchMembers();
    }
  };

  const handleInvite = async (e) => {
    e.preventDefault();
    setInviteError('');
    setInviteSuccess('');
    try {
      // inviteMember returns data directly
      const response = await teamService.inviteMember(inviteEmail, firstName, lastName);
      setInviteSuccess(response.message || 'Invitation sent successfully!');
      setInviteEmail('');
      setFirstName('');
      setLastName('');
      fetchMembers(); // Refresh the list of members
      setTimeout(() => {
        toggleModal();
        setInviteSuccess('');
      }, 2000);
    } catch (err) {
      const apiError = err?.response?.data?.error || err?.message || 'Failed to send invitation.';
      setInviteError(apiError);
    }
  };

  return (
    <>
      <div className="header bg-gradient-info pb-8 pt-5 pt-md-8" />
      <Container className="mt--7" fluid>
        <Row>
          <div className="col">
            <Card className="shadow">
              <CardHeader className="border-0">
                <Row className="align-items-center">
                  <Col xs="8">
                    <h3 className="mb-0">Manage Team</h3>
                  </Col>
                  <Col className="text-right" xs="4">
                    <Button color="primary" onClick={toggleModal} size="sm">
                      + Invite teammate
                    </Button>
                  </Col>
                </Row>
              </CardHeader>
              <CardBody>
                <Table className="align-items-center table-flush" responsive>
                  <thead className="thead-light">
                    <tr>
                      <th scope="col">Name</th>
                      <th scope="col">Email Address</th>
                      <th scope="col">Status</th>
                      <th scope="col">Role</th>
                      <th scope="col">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {teamMembers.map(member => (
                      <tr key={member.id}>
                        <td>{member.name}</td>
                        <td>{member.email}</td>
                        <td>{member.status}</td>
                        <td>{member.role}</td>
                        <td>
                          {member.role === 'Owner' ? (
                            <small className="text-muted">Owners can't be removed</small>
                          ) : member.status === 'Pending' ? (
                            <Button size="sm" disabled title="Invitation en attente">
                              Désactiver
                            </Button>
                          ) : (
                            <Button
                              size="sm"
                              color={member.status === 'Active' ? 'danger' : 'success'}
                              onClick={() => handleToggleActive(member)}
                              disabled={actionLoadingId === member.userId}
                              title={member.status === 'Active' ? 'Désactiver ce membre' : 'Activer ce membre'}
                            >
                              {actionLoadingId === member.userId ? '...' : (member.status === 'Active' ? 'Désactiver' : 'Activer')}
                            </Button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </CardBody>
            </Card>
          </div>
        </Row>
      </Container>

      <Modal isOpen={modal} toggle={toggleModal}>
        <ModalHeader toggle={toggleModal}>Invite a teammate</ModalHeader>
        <Form onSubmit={handleInvite}>
          <ModalBody>
            {inviteError && <Alert color="danger">{inviteError}</Alert>}
            {inviteSuccess && <Alert color="success">{inviteSuccess}</Alert>}
            <Alert color="info">
              <span className="alert-inner--icon"><i className="ni ni-like-2" /></span>
              <span className="alert-inner--text">
                <strong>Info&nbsp;!</strong> accédez à cette source de données et à Looker Studio avec votre compte Google.
              </span>
            </Alert>

            <FormGroup>
              <Label htmlFor="firstName">First Name</Label>
              <Input
                type="text"
                id="firstName"
                placeholder="Enter first name"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                required
              />
            </FormGroup>
            <FormGroup>
              <Label htmlFor="lastName">Last Name</Label>
              <Input
                type="text"
                id="lastName"
                placeholder="Enter last name"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                required
              />
            </FormGroup>
            <FormGroup>
              <Label htmlFor="inviteEmail">Email Address</Label>
              <Input
                type="email"
                id="inviteEmail"
                placeholder="Enter email address"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                required
              />
            </FormGroup>
          </ModalBody>
          <ModalFooter>
            <Button color="secondary" onClick={toggleModal}>Close</Button>
            <Button color="primary" type="submit">Invite teammate</Button>
          </ModalFooter>
        </Form>
      </Modal>
    </>
  );
};

export default ManageTeam;
