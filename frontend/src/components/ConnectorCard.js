import React from 'react';
import './ConnectorCard.css';

// Les icônes sont des composants SVG simples pour l'exemple.
// Dans un vrai projet, on utiliserait une bibliothèque comme react-icons.
const LinkIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
    <polyline points="15 3 21 3 21 9"></polyline>
    <line x1="10" y1="14" x2="21" y2="3"></line>
  </svg>
);

const RevokeIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"></circle>
    <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"></line>
  </svg>
);

const ConnectorCard = ({ title, subtitle, isActive, onOpen, onRevoke }) => {
  return (
    <div className="connector-card">
      <div className="card-header">
        <div className="card-icon"></div>
        <div className="card-title-group">
          <h3 className="card-title">{title}</h3>
          <p className="card-subtitle">{subtitle}</p>
        </div>
      </div>

      <div className="card-status">
        <span className={`status-indicator ${isActive ? 'active' : 'inactive'}`}></span>
        <p>{isActive ? 'Actived' : 'Deactivated'}</p>
      </div>

      <div className="card-actions">
        <button className="action-button" onClick={onOpen}>
          <LinkIcon />
          <span>open on Looker</span>
        </button>
        <button className="action-button revoke" onClick={onRevoke}>
          <RevokeIcon />
          <span>revoke authorization</span>
        </button>
      </div>
    </div>
  );
};

export default ConnectorCard;
