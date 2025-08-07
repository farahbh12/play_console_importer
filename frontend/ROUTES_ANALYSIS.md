# Analyse des Routes et Sidebars par Type d'Utilisateur

## Vue d'ensemble

Ce document présente l'analyse complète des routes et des sidebars correspondantes pour chaque type d'utilisateur dans l'application Play Console Importer.

## Types d'Utilisateurs et Rôles

### 1. **Administrateur (admin)**
- **Rôles**: `admin`, `administrateur`, `is_superuser`
- **Accès**: Complet - toutes les fonctionnalités
- **Layout**: `/admin/*`
- **Sidebar**: `AdminSidebar`

### 2. **Gestionnaire (manager)**
- **Rôles**: `manager`, `gestionnaire`
- **Accès**: Limité aux fonctions de gestion
- **Layout**: `/admin/*`
- **Sidebar**: `ManagerSidebar`

### 3. **Client (y compris Owner)**
- **Rôles**: `client`, `Owner`, `owner`
- **Accès**: Interface client uniquement
- **Layout**: `/client/*`
- **Sidebar**: `ClientSidebar`
- **Note**: Owner = Client propriétaire, pas administrateur

## Analyse Détaillée des Routes

### Routes Administrateur (AdminSidebar)

#### Section Principale
- `/admin/index` - Tableau de bord principal

#### Section Administration (Admin uniquement)
- `/admin/users` - Gestion des utilisateurs
- `/admin/settings` - Paramètres système

#### Section Gestion (Admin + Manager)
- `/admin/employees` - Gestion des employés
- `/admin/projects` - Gestion des projets
- `/admin/tasks` - Gestion des tâches
- `/admin/calendar` - Calendrier
- `/admin/reports` - Rapports

#### Section Abonnements
- `/admin/subscriptions` - Gestion des abonnements

#### Section GCS (Admin uniquement)
- `/admin/gcs/validate` - Validation GCS
- `/admin/gcs/display-files` - Fichiers GCS

#### Section Système (Admin uniquement)
- `/admin/logs` - Journaux système
- `/admin/backup` - Sauvegarde

### Routes Gestionnaire (ManagerSidebar)

#### Section Principale
- `/admin/index` - Tableau de bord

#### Section Gestion d'équipe
- `/admin/employees` - Gestion des employés
- `/admin/projects` - Projets
- `/admin/tasks` - Tâches
- `/admin/calendar` - Calendrier
- `/admin/reports` - Rapports

#### Section Paramètres
- `/admin/team-settings` - Paramètres d'équipe

### Routes Client (ClientSidebar)

#### Section Principale
- `/client/dashboard` - Tableau de bord client

#### Section Données
- `/client/data-source` - Source de données
- `/client/files` - Mes fichiers
- `/client/validate-uri` - Valider URI GCS

#### Section Compte
- `/client/profile` - Mon profil
- `/client/subscription` - Mon abonnement

## Logique de Redirection

### Après Connexion
```javascript
// Administrateur
if (userRole === 'admin') {
  redirectTo = '/admin/index';
  sidebar = 'AdminSidebar';
}

// Gestionnaire
if (userRole === 'manager') {
  redirectTo = '/admin/index';
  sidebar = 'ManagerSidebar';
}

// Client (y compris Owner)
if (userRole === 'client' || userRole === 'owner') {
  redirectTo = '/client/dashboard';
  sidebar = 'ClientSidebar';
}
```

### Protection des Routes
- **withRoleCheck()**: Vérifie les permissions avant d'accéder à une route
- **allowedRoles**: Définit quels rôles peuvent accéder à chaque route
- **ProtectedRoute**: Composant wrapper pour la protection des routes

## Structure des Sidebars

### AdminSidebar
```javascript
// Sections organisées par fonctionnalité
- Principal (Tableau de bord)
- Administration (Users, Settings)
- Gestion (Employees, Projects, Tasks, Calendar, Reports)
- Abonnements (Subscriptions)
- GCS (Validate, Files)
- Système (Logs, Backup)
```

### ManagerSidebar
```javascript
// Focus sur la gestion d'équipe
- Principal (Tableau de bord)
- Gestion d'équipe (Employees, Projects, Tasks, Calendar, Reports)
- Paramètres (Team Settings)
```

### ClientSidebar
```javascript
// Interface utilisateur final
- Principal (Dashboard)
- Données (Data Source, Files, Validate URI)
- Compte (Profile, Subscription)
```

## Configuration des Permissions

### Routes Admin Uniquement
- Gestion des utilisateurs
- Paramètres système
- Journaux système
- Sauvegarde
- Validation GCS
- Fichiers GCS

### Routes Admin + Manager
- Gestion des employés
- Projets
- Tâches
- Calendrier
- Rapports

### Routes Client Uniquement
- Toutes les routes `/client/*`
- Interface de données personnelles
- Gestion d'abonnement client

## Icônes et Couleurs

### Système d'Icônes Nucleo
- `ni ni-tv-2` - Tableau de bord (primary)
- `ni ni-single-02` - Utilisateurs (orange)
- `ni ni-badge` - Employés (yellow)
- `ni ni-bullet-list-67` - Projets (green)
- `ni ni-check-bold` - Tâches (info)
- `ni ni-calendar-grid-58` - Calendrier (pink)
- `ni ni-chart-bar-32` - Rapports (red)
- `ni ni-settings-gear-65` - Paramètres (cyan)
- `ni ni-archive-2` - Logs (red)
- `ni ni-cloud-upload-96` - Backup/GCS (warning/cyan)

### Couleurs par Rôle
- **Admin**: Bleu primary (`text-primary`)
- **Manager**: Vert success (`text-success`)
- **Client**: Orange (`text-orange`)

## Sécurité et Contrôle d'Accès

### Vérification des Rôles
1. **AuthContext**: Gère l'authentification et les rôles
2. **SidebarSwitcher**: Détermine quelle sidebar afficher
3. **withRoleCheck**: Protège les routes individuelles
4. **Layout Components**: Vérifient l'accès au niveau layout

### Gestion des Erreurs
- Redirection automatique si accès non autorisé
- Affichage de pages d'erreur appropriées
- Logs des tentatives d'accès non autorisées

## Clarification Importante : Rôle Owner

⚠️ **CORRECTION MAJEURE** : Le rôle "Owner" a été reclassé comme **CLIENT**, pas administrateur.

### Rôles Finaux :
- **administrateur/is_superuser** → admin (AdminSidebar, /admin/*)
- **gestionnaire/manager** → manager (ManagerSidebar, /admin/*) 
- **employee** → manager (ManagerSidebar, /admin/*)
- **client/Owner/owner** → client (ClientSidebar, /client/*)

### Logique Owner :
- Owner = **Client propriétaire** (pas administrateur)
- Accès à l'interface client uniquement
- Utilise ClientSidebar
- Redirection vers /client/dashboard
- Aucun privilège administrateur

## Conclusion

Cette architecture offre:
- **Séparation claire des responsabilités** par type d'utilisateur
- **Sécurité robuste** avec vérification des permissions
- **Interface intuitive** avec sidebars adaptées
- **Scalabilité** pour ajouter de nouveaux rôles/routes
- **Maintenance facilitée** avec code organisé par fonctionnalité
- **Classification correcte des rôles** avec Owner comme client propriétaire
