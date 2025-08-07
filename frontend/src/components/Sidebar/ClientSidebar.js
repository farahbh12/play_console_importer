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

  const clientRoutes = sidebarRoutes.filter(route => route.layout === '/client');

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
        
        {logo && (
          <NavbarBrand className="pt-0" to="/client/dashboard" tag={Link}>
            <img
              alt={logo.imgAlt}
              className="navbar-brand-img"
              src={logo.imgSrc}
            />
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
              {logo && (
                <Col className="collapse-brand" xs="6">
                  <Link to="/client/dashboard">
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
          
          <Nav navbar>{createLinks(clientRoutes)}</Nav>
          
          <hr className="my-3" />
          
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