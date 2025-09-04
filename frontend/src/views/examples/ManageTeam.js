import React, { useState, useEffect, useCallback } from 'react';
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
import { useAuth } from '../../contexts/AuthContext';

const ManageTeam = () => {
  const { currentUser } = useAuth();
  const [teamMembers, setTeamMembers] = useState([]);
  const [actionLoadingId, setActionLoadingId] = useState(null);

  const [modal, setModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');

  const [inviteError, setInviteError] = useState('');
  const [inviteSuccess, setInviteSuccess] = useState('');

  const toggleModal = () => setModal(!modal);

  const fetchMembers = useCallback(async () => {
    try {
      // Call the correct service (returns data directly)
      const membersData = await teamService.getTeamMembers();
      // Load connected client (owner) to override Owner row accurately
      let ownerClient = null;
      try {
        ownerClient = await clientService.getCurrent();
      } catch (e) {
        console.warn('Unable to load connected client for owner override:', e);
      }
      console.log('API Response Data:', membersData); // Debugging line
      const resolveOwnerName = () => {
        const src = ownerClient || currentUser || null;
        if (!src) return null;
        const fn =
          src.first_name ||
          src.prenom ||
          src.prenom_client ||
          src.firstName ||
          src?.user?.first_name ||
          src?.user?.firstName;
        const ln =
          src.last_name ||
          src.nom ||
          src.nom_client ||
          src.lastName ||
          src?.user?.last_name ||
          src?.user?.lastName;
        const composed = `${fn || ''} ${ln || ''}`.trim();
        // If composed empty, consider provided name fields or derive from email
        return (
          composed ||
          src.name ||
          src.full_name ||
          src.display_name ||
          src?.user?.name ||
          src?.user?.full_name ||
          nameFromEmail(src.email || src?.user?.email || '') ||
          null
        );
      };
      const resolveOwnerEmail = () => {
        const src = ownerClient || currentUser || null;
        if (!src) return null;
        return (
          src.email ||
          src?.user?.email ||

          null
        );
      };

      // Derive a readable name from an email local-part
      const nameFromEmail = (email) => {
        if (!email || typeof email !== 'string') return '';
        const local = email.split('@')[0];
        if (!local) return '';
        return local
          .replace(/[._-]+/g, ' ')
          .split(' ')
          .filter(Boolean)
          .map(part => part.charAt(0).toUpperCase() + part.slice(1))
          .join(' ');
      };

      const formattedMembers = membersData.map(m => {
        if (m.user && (m.role_client || m.role)) { // Active member or owner (Client model)
          const roleRaw = (m.role_client || m.role || '').toString();
          const isOwner = roleRaw.toLowerCase() === 'owner';
          const ownerName = isOwner ? resolveOwnerName() : null;
          const ownerEmail = isOwner ? resolveOwnerEmail() : null;
          // Prefer top-level client fields, then nested user fields, then email
          const fallbackFirst = m.first_name || m.prenom || m.firstName || m.user?.first_name || m.user?.firstName || '';
          const fallbackLast = m.last_name || m.nom || m.lastName || m.user?.last_name || m.user?.lastName || '';
          const fallbackComposed = `${fallbackFirst} ${fallbackLast}`.trim();
          const fallbackName = fallbackComposed || m.name || m.full_name || m.user?.name || m.user?.full_name || '';
          const fallbackEmail = m.email || m.user?.email;
          return {
            id: m.id,
            userId: m.user?.id,
            name: ownerName || fallbackName || nameFromEmail(fallbackEmail) || fallbackEmail,
            email: ownerEmail || fallbackEmail,
            // Status should not be 'Owner'; keep actual status or default Active
            status: m.status || 'Active',
            role: m.role_client || m.role
          };
        } else { // Pending invitation (Invitation model)
          const pendingEmail = m.email;
          const pendingName = `${m.first_name || ''} ${m.last_name || ''}`.trim();
          return {
            id: m.id,
            userId: null,
            name: pendingName || nameFromEmail(pendingEmail) || pendingEmail,
            email: pendingEmail,
            status: 'Pending',
            role: 'MEMBRE_INVITE'
          };
        }
      });
      setTeamMembers(formattedMembers);
    } catch (err) {
      console.error('Failed to fetch team members:', err);
    } finally {
      // no-op
    }
  }, [currentUser]);

  useEffect(() => {
    fetchMembers();
    // Re-fetch when currentUser is set to ensure Owner row uses connected owner's data
  }, [fetchMembers]);

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
