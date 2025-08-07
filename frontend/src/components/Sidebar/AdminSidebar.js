import React, { useState } from "react";
import { NavLink as NavLinkRRD, Link, useLocation } from "react-router-dom";
import PropTypes from "prop-types";
import {
  Navbar,
  Container,
  Nav,
  NavItem,
  NavLink,
  Collapse,
  NavbarBrand,
  UncontrolledDropdown,
  DropdownToggle,
  DropdownMenu,
  DropdownItem,
  Media,
  Row,
  Col
} from "reactstrap";

const AdminSidebar = ({ user, logo }) => {
  const [collapseOpen, setCollapseOpen] = useState(false);
  const location = useLocation();

  const activeRoute = (routeName) => {
    return location.pathname === routeName ? "active" : "";
  };

  const toggleCollapse = () => {
    setCollapseOpen(!collapseOpen);
  };

  const closeCollapse = () => {
    setCollapseOpen(false);
  };

  // Routes complètes pour les administrateurs (accès total)
  const adminRoutes = [
    {
      path: "/admin/index",
      name: "Tableau de bord",
      icon: "ni ni-tv-2 text-primary",
      section: "principal"
    },
    // Administration - Routes admin uniquement
   
   
    // Gestion des employés
    {
      path: "/admin/employees",
      name: "Liste des employés",
      icon: "ni ni-single-02 text-orange",
      section: "gestion"
    },
    // Gestion des clients
    {
      path: "/admin/clients",
      name: "Liste des clients",
      icon: "ni ni-badge text-blue",
      section: "gestion"
    },
    // Gestion des abonnements
    {
      path: "/admin/subscriptions",
      name: "Liste des abonnements",
      icon: "ni ni-credit-card text-green",
      section: "gestion"
    },
   
  ];

  // Routes système - Admin uniquement
  const systemRoutes = [
   
  ];

  const allRoutes = [...adminRoutes, ...systemRoutes];

  const createLinks = (routes) => {
    return routes.map((prop, key) => {
      return (
        <NavItem key={key}>
          <NavLink
            to={prop.path}
            tag={NavLinkRRD}
            onClick={closeCollapse}
            className={({ isActive }) => isActive ? "active" : ""}
            end
          >
            <i className={prop.icon} />
            {prop.name}
          </NavLink>
        </NavItem>
      );
    });
  };

  return (
    <Navbar
      className="navbar-vertical fixed-left navbar-light bg-white"
      expand="md"
      id="sidenav-main"
    >
      <Container fluid>
        <button
          className="navbar-toggler"
          type="button"
          onClick={toggleCollapse}
        >
          <span className="navbar-toggler-icon" />
        </button>
        
        {logo ? (
          <NavbarBrand className="pt-0" to="/admin/index" tag={Link}>
            <img
              alt={logo.imgAlt}
              className="navbar-brand-img"
              src={logo.imgSrc}
            />
          </NavbarBrand>
        ) : (
          <NavbarBrand className="pt-0" to="/admin/index" tag={Link}>
            <h2 className="text-primary font-weight-bold">Admin Panel</h2>
          </NavbarBrand>
        )}
        
        <Nav className="align-items-center d-md-none">
          <UncontrolledDropdown nav>
            <DropdownToggle nav>
              <Media className="align-items-center">
                <span className="avatar avatar-sm rounded-circle bg-default">
                  <i className="ni ni-single-02 text-white" />
                </span>
              </Media>
            </DropdownToggle>
            <DropdownMenu className="dropdown-menu-arrow" right>
              <DropdownItem className="noti-title" header tag="div">
                <h6 className="text-overflow m-0">Bienvenue !</h6>
              </DropdownItem>
              <DropdownItem to="/admin/profile" tag={Link}>
                <i className="ni ni-single-02" />
                <span>Mon profil</span>
              </DropdownItem>
              <DropdownItem divider />
              <DropdownItem to="/auth/logout" tag={Link}>
                <i className="ni ni-user-run" />
                <span>Déconnexion</span>
              </DropdownItem>
            </DropdownMenu>
          </UncontrolledDropdown>
        </Nav>
        
        <Collapse navbar isOpen={collapseOpen}>
          <div className="navbar-collapse-header d-md-none">
            <Row>
              {logo && (
                <Col className="collapse-brand" xs="6">
                  <Link to="/admin/index">
                    <img alt={logo.imgAlt} src={logo.imgSrc} />
                  </Link>
                </Col>
              )}
              <Col className="collapse-close" xs="6">
                <button
                  className="navbar-toggler"
                  type="button"
                  onClick={toggleCollapse}
                >
                  <span />
                  <span />
                </button>
              </Col>
            </Row>
          </div>
          
          {/* Routes principales */}
          <Nav navbar>
            {createLinks(adminRoutes.filter(route => route.section === 'principal'))}
          </Nav>
          
          
          <Nav navbar>
            {createLinks(adminRoutes.filter(route => route.section === 'administration'))}
          </Nav>
          
          <hr className="my-3" />
          <h6 className="navbar-heading text-muted">Gestion</h6>
          <Nav navbar>
            {createLinks(adminRoutes.filter(route => route.section === 'gestion'))}
          </Nav>
          
          
          <Nav navbar>
            {createLinks(adminRoutes.filter(route => route.section === 'business'))}
          </Nav>
          
          
          <Nav navbar>
            {createLinks(adminRoutes.filter(route => route.section === 'gcs'))}
          </Nav>
          
          
          <Nav navbar>
            {createLinks(systemRoutes)}
          </Nav>
          
          <hr className="my-3" />
          
          <NavLink 
            to="/admin/profile" 
            tag={NavLinkRRD} 
            className="d-flex align-items-center p-3 text-decoration-none"
            onClick={closeCollapse}
          >
            <div className="avatar avatar-xl bg-default rounded-circle mr-3">
              <i className="ni ni-single-02 text-white" style={{ fontSize: '1.5rem', lineHeight: '3rem' }} />
            </div>
            <div>
              <h6 className="mb-0 text-dark">{user?.first_name || 'Administrateur'}</h6>
              <small className="text-muted">Voir le profil</small>
            </div>
          </NavLink>
        </Collapse>
      </Container>
    </Navbar>
  );
};

AdminSidebar.defaultProps = {
  user: {
    first_name: 'Administrateur'
  },
  logo: {
    imgSrc: require("../../assets/img/brand/argon-react.png"),
    imgAlt: "Logo"
  }
};

AdminSidebar.propTypes = {
  user: PropTypes.shape({
    first_name: PropTypes.string,
    email: PropTypes.string,
    avatar: PropTypes.string
  }),
  logo: PropTypes.shape({
    imgSrc: PropTypes.string,
    imgAlt: PropTypes.string
  })
};

export default AdminSidebar;
