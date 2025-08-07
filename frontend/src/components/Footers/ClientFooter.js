import React from "react";
import { Link } from "react-router-dom";

const ClientFooter = () => {
  return (
    <footer className="footer pt-0">
      <div className="row align-items-center justify-content-lg-between">
        <div className="col-lg-6">
          <div className="copyright text-center text-lg-left text-muted">
            {new Date().getFullYear()}{" "}
            <Link
              className="font-weight-bold ml-1"
              to="/"
            >
              Play Console Importer
            </Link>
          </div>
        </div>
        <div className="col-lg-6">
          <ul className="nav nav-footer justify-content-center justify-content-lg-end">
            <li className="nav-item">
              <Link
                className="nav-link"
                to="/about"
              >
                À propos
              </Link>
            </li>
            <li className="nav-item">
              <Link
                className="nav-link"
                to="/blog"
              >
                Blog
              </Link>
            </li>
            <li className="nav-item">
              <Link
                className="nav-link"
                to="/license"
              >
                Licence
              </Link>
            </li>
          </ul>
        </div>
      </div>
    </footer>
  );
};

export default ClientFooter;
