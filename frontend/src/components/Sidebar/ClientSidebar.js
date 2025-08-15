import React, { useState } from "react";
import { sidebarRoutes } from "../../routes";
import { NavLink as NavLinkRRD, Link } from "react-router-dom";
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

const ClientSidebar = ({ user, logo }) => {
  const [collapseOpen, setCollapseOpen] = useState(false);
  const toggleCollapse = () => {
    setCollapseOpen(!collapseOpen);
  };

  const closeCollapse = () => {
    setCollapseOpen(false);
  };

  const mainRoutes = sidebarRoutes.filter(route => route.layout === '/client' && !route.path.includes('profile') && !route.path.includes('manage-team') && !route.path.includes('subscription'));
  const managementRoutes = sidebarRoutes.filter(route => route.path.includes('manage-team'));
  const accountRoutes = sidebarRoutes.filter(route => route.path.includes('profile') || route.path.includes('subscription'));

  const isInvited = user?.role === 'MEMBRE_INVITE';
  const invitedAllowed = ['/client/source', '/client/destination', '/client/profile'];

  const createLinks = (routes) => {
    return routes.map((prop, key) => {
      const isBlockedForInvited = isInvited && !invitedAllowed.includes(prop.path);
      const commonProps = {
        onClick: (e) => {
          if (isBlockedForInvited) {
            e.preventDefault();
            return;
          }
          closeCollapse();
        },
        className: ({ isActive }) => {
          const base = isActive ? 'active' : '';
          return isBlockedForInvited ? base + ' disabled' : base;
        },
        end: true,
        title: isBlockedForInvited ? 'Accès restreint' : undefined,
        style: isBlockedForInvited ? { opacity: 0.6, cursor: 'not-allowed' } : undefined,
      };

      return (
        <NavItem key={key}>
          <NavLink to={prop.path} tag={NavLinkRRD} {...commonProps}>
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
        
        <NavbarBrand className="pt-0 d-flex align-items-baseline" to="/client/dashboard" tag={Link}>
          <span className="fw-bold" style={{ fontSize: '1.25rem' }}>DataDock</span>
          <small className="text-uppercase ms-2" style={{ opacity: 0.8 }}>ReportApp</small>
        </NavbarBrand>
        
        <Nav className="align-items-center d-md-none">
          <UncontrolledDropdown nav>
            <DropdownToggle nav>
              <Media className="align-items-center">
                <span className="avatar avatar-sm rounded-circle bg-default">
                  <i className="ni ni-single-02 text-white" />
                </span>
              </Media>
            </DropdownToggle>
            <DropdownMenu className="dropdown-menu-arrow" end>
              <DropdownItem className="noti-title" header tag="div">
                <h6 className="text-overflow m-0">Bienvenue !</h6>
              </DropdownItem>
              <DropdownItem to="/client/profile" tag={Link}>
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
              <Col className="collapse-brand" xs="6">
                <Link to="/client/dashboard" style={{ textDecoration: 'none' }}>
                  <span className="fw-bold">DataDock</span>
                  <small className="text-uppercase ms-1" style={{ opacity: 0.8 }}>ReportApp</small>
                </Link>
              </Col>
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
          
          <h6 className="navbar-heading text-muted">Navigation</h6>
          <Nav navbar>{createLinks(mainRoutes)}</Nav>

          <hr className="my-3" />
          <h6 className="navbar-heading text-muted">Gestion</h6>
          <Nav className="mb-md-3" navbar>
            {createLinks(managementRoutes)}
          </Nav>

          <hr className="my-3" />
          <h6 className="navbar-heading text-muted">Mon Compte</h6>
          <Nav className="mb-md-3" navbar>
            {createLinks(accountRoutes)}
          </Nav>
          <NavLink 
            to="/client/profile" 
            tag={NavLinkRRD} 
            className="d-flex align-items-center p-3 text-decoration-none"
            onClick={closeCollapse}
          >
            <div className="avatar avatar-xl bg-default rounded-circle mr-3">
              <i className="ni ni-single-02 text-white" style={{ fontSize: '1.5rem', lineHeight: '3rem' }} />
            </div>
            <div>
              <h6 className="mb-0 text-dark">{user?.name || 'Client'}</h6>
              <small className="text-muted">Voir le profil</small>
            </div>
          </NavLink>
        </Collapse>
      </Container>
    </Navbar>
  );
};

ClientSidebar.defaultProps = {
  user: {
    name: 'Client'
  },
  logo: {
    imgSrc: require("../../assets/img/brand/argon-react.png"),
    imgAlt: "Logo"
  }
};

ClientSidebar.propTypes = {
  user: PropTypes.shape({
    name: PropTypes.string,
    email: PropTypes.string,
    avatar: PropTypes.string
  }),
  logo: PropTypes.shape({
    imgSrc: PropTypes.string,
    imgAlt: PropTypes.string
  })
};

export default ClientSidebar;