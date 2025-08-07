import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  DropdownMenu,
  DropdownItem,
  UncontrolledDropdown,
  DropdownToggle,
  Navbar,
  Nav,
  Container,
  Media,
  Button
} from "reactstrap";
import authService from "../../services/auth";
import clientService from "../../services/clientService";

const ClientNavbar = ({ onLogout }) => {
  const [userData, setUserData] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUserData = async () => {
      const user = authService.getCurrentUser();
      if (!user) return;

      if (user.user_type === 'client' || user.role === 'client' || user.role === 'Owner' || user.role === 'owner') {
        try {
          const clientData = await clientService.getCurrent();
          setUserData(clientData);
        } catch (error) {
          console.error("Erreur lors du chargement des données client pour la navbar:", error);
          setUserData(user); // Fallback
        }
      } else {
        setUserData(user);
      }
    };

    fetchUserData();
  }, []);

  const handleLogout = () => {
    authService.logout();
    if (onLogout) onLogout();
    navigate("/auth/login");
  };

  const handleProfileClick = () => {
    navigate("/client/profile");
  };

  const displayName = (userData?.first_name && userData?.last_name)
    ? `${userData.first_name} ${userData.last_name}`
    : userData?.email || 'Utilisateur';

  return (
    <>
      <Navbar className="navbar-top navbar-dark" expand="md" id="navbar-main">
        <Container fluid>
          <Button
            color="link"
            className="h4 mb-0 text-white text-uppercase d-none d-lg-inline-block p-0 border-0 bg-transparent"
            onClick={() => navigate('/client/dashboard')}
          >
            Tableau de bord client
          </Button>
          
          <Nav className="align-items-center d-none d-md-flex" navbar>
            <UncontrolledDropdown nav>
              <DropdownToggle className="pr-0" nav>
                <Media className="align-items-center">
                  <span className="avatar avatar-sm rounded-circle">
                    <i className="ni ni-circle-08" />
                  </span>
                  <Media className="ml-2 d-none d-lg-block">
                    <span className="mb-0 text-sm font-weight-bold">
                      {displayName}
                    </span>
                  </Media>
                </Media>
              </DropdownToggle>
              <DropdownMenu className="dropdown-menu-arrow" right>
                <DropdownItem className="noti-title" header tag="div">
                  <h6 className="text-overflow m-0">Bienvenue !</h6>
                </DropdownItem>
                <DropdownItem href="#" onClick={handleProfileClick}>
                  <i className="ni ni-single-02" />
                  <span>Mon profil</span>
                </DropdownItem>
                <DropdownItem href="#" onClick={() => navigate('/client/profile-edit')}>
                  <i className="ni ni-settings-gear-65" />
                  <span>Modifier profil</span>
                </DropdownItem>
                <DropdownItem divider />
                <DropdownItem href="#" onClick={handleLogout}>
                  <i className="ni ni-user-run" />
                  <span>Déconnexion</span>
                </DropdownItem>
              </DropdownMenu>
            </UncontrolledDropdown>
          </Nav>
        </Container>
      </Navbar>
    </>
  );
};

export default ClientNavbar;
