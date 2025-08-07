import React, { useEffect, useState } from 'react';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import {
  Card, CardHeader, Table, Container, 
  Row, Col, CardBody, Spinner, 
  Alert, Button, ButtonGroup
} from 'reactstrap';
import employeeService from '../../services/employeeService';

const EmployeeList = () => {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [updating, setUpdating] = useState({});

  // Récupérer la liste des employés depuis la table Employee
  const fetchEmployees = async () => {
    try {
      const data = await employeeService.getAll();
      console.log('Données des employés:', data);
      
      // Formater les données des employés
      const formattedEmployees = data.map(emp => ({
        id: emp.id,
        // Utiliser les champs de l'API avec fallback sur les anciens champs
        first_name: emp.first_name || emp.prenom || emp.user?.first_name || '',
        last_name: emp.last_name || emp.nom || emp.user?.last_name || '',
        email: emp.email || emp.user?.email || '',
        // Utiliser le champ role_employe qui contient le rôle affiché
        role: emp.role_employe || emp.role || 'Employé',
        is_active: emp.is_active !== false, // Par défaut actif si non spécifié
        created_at: emp.created_at,
        updated_at: emp.updated_at
      }));
      
      // Filtrer les administrateurs
      const filteredEmployees = formattedEmployees.filter(
        emp => !emp.role.toLowerCase().includes('administrateur') && 
               !emp.role.toLowerCase().includes('admin')
      );
      
      setEmployees(filteredEmployees);
    } catch (err) {
      console.error('Erreur détaillée:', err);
      setError("Erreur lors du chargement des employés. Veuillez réessayer.");
      toast.error("Erreur lors du chargement des employés");
    } finally {
      setLoading(false);
    }
  };

  // Gérer l'activation/désactivation d'un employé
  const handleStatusUpdate = async (employeeId, activate) => {
    const action = activate ? 'activating' : 'deactivating';
    const successMessage = activate ? 'activé' : 'désactivé';
    
    try {
      // Mise à jour optimiste de l'interface
      setEmployees(prev => 
        prev.map(emp => 
          emp.id === employeeId 
            ? { ...emp, is_active: activate } 
            : emp
        )
      );
      
      // Désactiver le bouton pendant la requête
      setUpdating(prev => ({ ...prev, [employeeId]: action }));
      
      // Appel API
      if (activate) {
        await employeeService.activate(employeeId);
      } else {
        await employeeService.deactivate(employeeId);
      }
      
      toast.success(`Compte ${successMessage} avec succès`);
      
    } catch (error) {
      console.error(`Erreur lors de la ${action} du compte:`, error);
      toast.error(`Erreur lors de la ${action} du compte`);
      
      // En cas d'erreur, on remet l'ancienne valeur
      setEmployees(prev => 
        prev.map(emp => 
          emp.id === employeeId 
            ? { ...emp, is_active: !activate } // Inverser le statut
            : emp
        )
      );
    } finally {
      // Réactiver le bouton
      setUpdating(prev => ({ ...prev, [employeeId]: false }));
    }
  };

  // Charger les employés au montage du composant
  useEffect(() => {
    fetchEmployees();
  }, []);

  return (
    <>
      <div className="header bg-gradient-info pb-8 pt-5 pt-md-8">
        <Container fluid>
          <div className="header-body" />
        </Container>
      </div>
      
      <Container className="mt--7" fluid>
        <Row>
          <div className="col">
            <Card className="shadow">
              <CardHeader className="border-0">
                <Row className="align-items-center">
                  <Col xs="8">
                    <h3 className="mb-0">Liste des employés</h3>
                  </Col>
                </Row>
              </CardHeader>

              {loading ? (
                <div className="text-center my-4">
                  <Spinner color="primary" />
                </div>
              ) : error ? (
                <Alert color="danger">{error}</Alert>
              ) : employees.length === 0 ? (
                <Alert color="info">Aucun employé trouvé.</Alert>
              ) : (
                <Table className="align-items-center table-flush" responsive>
                  <thead className="thead-light">
                    <tr>
                      <th>Nom</th>
                      <th>Prénom</th>
                      <th>Email</th>
                      <th>Rôle</th>
                      <th>Statut</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {employees.map((employee) => {
                      const isActive = employee.is_active === true;
                      
                      return (
                        <tr key={employee.id}>
                          <td>{employee.last_name || employee.nom || '—'}</td>
                          <td>{employee.first_name || employee.prenom || '—'}</td>
                          <td>{employee.email || '—'}</td>
                          <td>{employee.role || '—'}</td>
                          <td>
                            <span className={`badge ${isActive ? 'badge-success' : 'badge-danger'}`}>
                              {isActive ? 'Actif' : 'Inactif'}
                            </span>
                          </td>
                          <td>
                            <ButtonGroup>
                              <Button
                                color="success"
                                size="sm"
                                onClick={() => handleStatusUpdate(employee.id, true)}
                                disabled={updating[employee.id] || employee.is_active === true}
                                className="mr-1"
                              >
                                {updating[employee.id] === 'activating' ? (
                                  <Spinner size="sm" />
                                ) : (
                                  'Activer'
                                )}
                              </Button>
                              <Button
                                color="danger"
                                size="sm"
                                onClick={() => handleStatusUpdate(employee.id, false)}
                                disabled={updating[employee.id] || employee.is_active === false}
                              >
                                {updating[employee.id] === 'deactivating' ? (
                                  <Spinner size="sm" />
                                ) : (
                                  'Désactiver'
                                )}
                              </Button>
                            </ButtonGroup>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </Table>
              )}

              <CardBody>
                {/* Emplacement pour la pagination si nécessaire */}
              </CardBody>
            </Card>
          </div>
        </Row>
      </Container>
    </>
  );
};

export default EmployeeList;