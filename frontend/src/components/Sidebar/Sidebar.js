import React, { useState, useMemo } from "react";
import { NavLink as NavLinkRRD, Link } from "react-router-dom";
import { PropTypes } from "prop-types";
import { useAuth } from "../../contexts/AuthContext";
import { getUserRole } from "../../routes";

// reactstrap components
import {
  NavItem,
  NavLink,
  Nav,
  Collapse,
  Media,
  NavbarText,
  Row,
  Col
} from "reactstrap";

const Sidebar = (props) => {
  const [collapseOpen, setCollapseOpen] = useState();
  
  
  // Utilisation sécurisée de useAuth
  let currentUser = null;
  try {
    const auth = useAuth();
    currentUser = auth.currentUser;
  } catch (error) {
    console.error("Erreur d'authentification:", error);
  }

  const toggleCollapse = () => setCollapseOpen((data) => !data);
  const closeCollapse = () => setCollapseOpen(false);

  // Vérifie si l'utilisateur a la permission d'accéder à une route
  const hasPermission = (route) => {
    if (!route.allowedRoles) return true;
    if (!currentUser) return false;
    
    const userRole = getUserRole(currentUser);
    
    // Si l'utilisateur est gestionnaire et que la route est pour admin
    if (userRole === 'manager' && route.allowedRoles.includes('admin')) {
      return true;
    }
    
    return route.allowedRoles.includes(userRole);
  };

  // Groupe les routes par section
  const groupedRoutes = useMemo(() => {
    if (!props.routes) return [];
    
    const sections = {};
    
    // Filtrer d'abord les routes accessibles
    const accessibleRoutes = props.routes.filter(route => 
      route.name && hasPermission(route)
    );
    
    // Grouper par section
    accessibleRoutes.forEach(route => {
      const section = route.section || 'Autre';
      if (!sections[section]) {
        sections[section] = [];
      }
      sections[section].push(route);
    });
    
    return sections;
  }, [props.routes, currentUser]);

  // Crée les liens de navigation
  const createLinks = (routes) => {
    if (!routes) return null;
    
    return routes.map((prop, key) => (
      <NavItem key={key}>
        <NavLink
          to={prop.layout + prop.path}
          tag={NavLinkRRD}
          onClick={closeCollapse}
          activeClassName="active"
          className="d-flex align-items-center"
        >
            <i className={prop.icon} />
            {prop.name}
          </NavLink>
        </NavItem>
      ));
  };

  const { routes, logo } = props;
  
  return (
    <div className="sidebar">
      <div className="sidebar-wrapper">
        {logo && (
          <div className="navbar-brand">
            <Link to="/admin/index">
              <img alt={logo.imgAlt} className="navbar-brand-img" src={logo.imgSrc} />
            </Link>
          </div>
        )}

        <button className="navbar-toggler" type="button" onClick={toggleCollapse}>
          <span className="navbar-toggler-icon" />
        </button>

        <Collapse isOpen={collapseOpen} navbar>
          <Nav navbar>
            {Object.entries(groupedRoutes).map(([section, routes]) => (
              <React.Fragment key={section}>
                {/* En-tête de section */}
                {section !== 'undefined' && section !== 'Autre' && (
                  <div className="sidebar-section">
                    <h6 className="text-uppercase text-xs text-muted font-weight-bolder px-3 mb-2">
                      {section}
                    </h6>
                  </div>
                )}
                
                {/* Liens de la section */}
                {routes.map((route, index) => (
                  <NavItem key={index}>
                    <NavLink
                      to={route.layout + route.path}
                      tag={NavLinkRRD}
                      onClick={closeCollapse}
                      activeClassName="active"
                      className="d-flex align-items-center"
                    >
                      <i className={`${route.icon} mr-3`} />
                      <span>{route.name}</span>
                    </NavLink>
                  </NavItem>
                ))}
                
                {/* Espacement entre les sections */}
                <div className="mb-3" />
              </React.Fragment>
            ))}
          </Nav>
          
          <hr className="my-3" />
          
          {currentUser && (
            <div className="mt-4">
              <Media className="align-items-center">
                <Media>
                  <span className="avatar rounded-circle">
                    <i className="ni ni-circle-08" />
                  </span>
                </Media>
                <Media className="ml-2 d-none d-lg-block">
                  <span className="mb-0 text-sm font-weight-bold">
                    {currentUser.email}
                  </span>
                </Media>
              </Media>
            </div>
          )}
        </Collapse>
      </div>
    </div>
  );
};

Sidebar.defaultProps = {
  routes: [],
};

Sidebar.propTypes = {
  toggleSidebar: PropTypes.func,
  bgColor: PropTypes.oneOf(["primary", "blue", "green"]),
  logo: PropTypes.shape({
    innerLink: PropTypes.string,
    outterLink: PropTypes.string,
    imgSrc: PropTypes.string.isRequired,
    imgAlt: PropTypes.string,
  }),
  routes: PropTypes.arrayOf(PropTypes.object),
};

export default Sidebar;
