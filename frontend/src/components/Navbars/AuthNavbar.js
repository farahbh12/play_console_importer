/*!

=========================================================
* Argon Dashboard React - v1.2.4
=========================================================

* Product Page: https://www.creative-tim.com/product/argon-dashboard-react
* Copyright 2024 Creative Tim (https://www.creative-tim.com)
* Licensed under MIT (https://github.com/creativetimofficial/argon-dashboard-react/blob/master/LICENSE.md)

* Coded by Creative Tim

=========================================================

* The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

*/
import { Link } from "react-router-dom";
// reactstrap components
import {
  UncontrolledCollapse,
  NavbarBrand,
  Navbar,
  NavItem,
  NavLink,
  Nav,
  Container,
  Row,
  Col,
} from "reactstrap";

const AdminNavbar = () => {
  return (
    <>
      <Navbar className="navbar-top navbar-horizontal navbar-dark" expand="md">
        <Container className="px-4">
          <NavbarBrand to="/" tag={Link} className="d-flex align-items-center">
            <span
              className="d-inline-flex align-items-center justify-content-center rounded"
              style={{ width: 28, height: 28, border: '1px solid currentColor', fontSize: 12, marginRight: 10 }}
            >
              DD
            </span>
            <span style={{ fontWeight: 700, letterSpacing: 0.4 }}>DataDock</span>
            <span className="mx-2" aria-hidden style={{ opacity: 0.5 }}>/</span>
            <span className="text-uppercase" style={{ fontSize: 12, opacity: 0.8, letterSpacing: 1 }}>ReportApp</span>
          </NavbarBrand>
          <button className="navbar-toggler" id="navbar-collapse-main">
            <span className="navbar-toggler-icon" />
          </button>
          <UncontrolledCollapse navbar toggler="#navbar-collapse-main">
            <div className="navbar-collapse-header d-md-none">
              <Row>
                <Col className="collapse-brand" xs="6">
                  <Link to="/" style={{ textDecoration: 'none' }}>
                    <span
                      className="d-inline-flex align-items-center justify-content-center rounded"
                      style={{ width: 24, height: 24, border: '1px solid currentColor', fontSize: 10, marginRight: 8 }}
                    >
                      DD
                    </span>
                    <span style={{ fontWeight: 700, letterSpacing: 0.4 }}>DataDock</span>
                    <span className="mx-1" aria-hidden style={{ opacity: 0.5 }}>/</span>
                    <span className="text-uppercase" style={{ fontSize: 11, opacity: 0.8, letterSpacing: 1 }}>ReportApp</span>
                  </Link>
                </Col>
                <Col className="collapse-close" xs="6">
                  <button className="navbar-toggler" id="navbar-collapse-main">
                    <span />
                    <span />
                  </button>
                </Col>
              </Row>
            </div>
            <Nav className="ml-auto" navbar>
              <NavItem>
                <NavLink className="nav-link-icon" to="/" tag={Link}>
                  <i className="ni ni-planet" />
                  <span className="nav-link-inner--text">Dashboard</span>
                </NavLink>
              </NavItem>
              <NavItem>
                <NavLink
                  className="nav-link-icon"
                  to="/auth/register"
                  tag={Link}
                >
                  <i className="ni ni-circle-08" />
                  <span className="nav-link-inner--text">Register</span>
                </NavLink>
              </NavItem>
              <NavItem>
                <NavLink className="nav-link-icon" to="/auth/login" tag={Link}>
                  <i className="ni ni-key-25" />
                  <span className="nav-link-inner--text">Login</span>
                </NavLink>
              </NavItem>
              <NavItem>
                <NavLink
                  className="nav-link-icon"
                  to="/admin/user-profile"
                  tag={Link}
                >
                  <i className="ni ni-single-02" />
                  <span className="nav-link-inner--text">Profile</span>
                </NavLink>
              </NavItem>
            </Nav>
          </UncontrolledCollapse>
        </Container>
      </Navbar>
    </>
  );
};

export default AdminNavbar;
