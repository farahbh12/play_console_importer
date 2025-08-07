import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import authService from "../../services/auth";
import employeeService from "../../services/employeeService";
import {
  DropdownMenu,
  DropdownItem,
  UncontrolledDropdown,
  DropdownToggle,
  Navbar,
  Nav,
  Container,
  Media,
} from "reactstrap";

const AdminNavbar = (props) => {
  const [employeeData, setEmployeeData] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchEmployeeData = async () => {
      try {
        const data = await employeeService.getCurrent();
        setEmployeeData(data);
      } catch (error) {
        console.error("Erreur lors de la récupération des données de l'employé:", error);
        // En cas d'erreur, utiliser les données de base de l'utilisateur connecté
        setEmployeeData(authService.getCurrentUser());
      }
    };

    fetchEmployeeData();
  }, []);

  const handleLogout = () => {
    authService.logout();
    navigate('/auth/login');
  };

  const getDisplayName = () => {
    if (!employeeData) return "Chargement...";

    // Les données de l'employé (first_name, last_name) ont la priorité
    if (employeeData.first_name && employeeData.last_name) {
      return `${employeeData.first_name} ${employeeData.last_name}`;
    }

    // Fallback sur les données de l'objet user imbriqué (rétrocompatibilité)
    if (employeeData.user?.first_name && employeeData.user?.last_name) {
      return `${employeeData.user.first_name} ${employeeData.user.last_name}`;
    }

    // Fallback final sur l'email
    return employeeData.email || 'Employé';
  };

  return (
    <>
      <Navbar className="navbar-top navbar-dark" expand="md" id="navbar-main">
        <Container fluid>
          <span className="h4 mb-0 text-white text-uppercase d-none d-lg-inline-block">
            {props.brandText}
          </span>
          <Nav className="align-items-center d-none d-md-flex" navbar>
            <UncontrolledDropdown nav>
              <DropdownToggle className="pr-0" nav>
                <Media className="align-items-center">
                  <span className="avatar avatar-sm rounded-circle">
                     <i className="ni ni-circle-08" />
                  </span>
                  <Media className="ml-2 d-none d-lg-block">
                    <span className="mb-0 text-sm font-weight-bold">
                      {getDisplayName()}
                    </span>
                  </Media>
                </Media>
              </DropdownToggle>
              <DropdownMenu className="dropdown-menu-arrow" right>
                <DropdownItem className="noti-title" header tag="div">
                  <h6 className="text-overflow m-0">Bienvenue !</h6>
                </DropdownItem>
                <DropdownItem onClick={() => navigate('/admin/profile')}> 
                  <i className="ni ni-single-02" />
                  <span>Mon profil</span>
                </DropdownItem>
                <DropdownItem onClick={() => navigate('/admin/profile-edit')}>
                  <i className="ni ni-settings-gear-65" />
                  <span>Modifier profil</span>
                </DropdownItem>
                <DropdownItem divider />
                <DropdownItem onClick={handleLogout}>
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

export default AdminNavbar;