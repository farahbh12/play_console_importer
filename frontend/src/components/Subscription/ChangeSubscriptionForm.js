import React, { useState, useEffect } from 'react';
import {
  Button,
  Dialog,
  DialogHeader,
  DialogBody,
  DialogFooter,
  Select,
  Option,
  Textarea,
  Typography,
  Alert,
  Spinner
} from "@material-tailwind/react";
import { FaCheckCircle, FaTimesCircle } from 'react-icons/fa';
import subscriptionService from '../../services/subscription';

export function ChangeSubscriptionForm({ clientId, currentPlan, isOpen, onClose, onSuccess }) {
  const [newPlan, setNewPlan] = useState('');
  const [reason, setReason] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Liste des plans disponibles (à remplacer par un appel API si nécessaire)
  const availablePlans = [
    { id: 'BASIC', name: 'Basic' },
    { id: 'PRO', name: 'Professionnel' },
    { id: 'ENTERPRISE', name: 'Entreprise' }
  ].filter(plan => plan.id !== currentPlan);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!newPlan) {
      setError('Veuillez sélectionner un nouveau forfait');
      return;
    }
    
    setIsLoading(true);
    setError('');
    setSuccess('');
    
    try {
      await subscriptionService.requestSubscriptionChange(clientId, newPlan, reason);
      setSuccess('Votre demande de modification a été envoyée avec succès. Un administrateur la traitera sous peu.');
      onSuccess && onSuccess();
    } catch (err) {
      setError(err.response?.data?.error || 'Une erreur est survenue lors de l\'envoi de la demande');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} handler={onClose} size="md">
      <DialogHeader>Modifier mon abonnement</DialogHeader>
      <form onSubmit={handleSubmit}>
        <DialogBody divider className="flex flex-col gap-4">
          <Typography variant="h6" color="blue-gray">
            Forfait actuel: <span className="font-bold">
              {currentPlan === 'BASIC' ? 'Basic' : 
               currentPlan === 'PRO' ? 'Professionnel' : 
               currentPlan === 'ENTERPRISE' ? 'Entreprise' : currentPlan}
            </span>
          </Typography>
          
          <div>
            <Typography variant="small" color="blue-gray" className="mb-1 font-medium">
              Nouveau forfait *
            </Typography>
            <Select
              label="Sélectionner un forfait"
              value={newPlan}
              onChange={(value) => setNewPlan(value)}
              disabled={isLoading}
            >
              {availablePlans.map((plan) => (
                <Option key={plan.id} value={plan.id}>
                  {plan.name}
                </Option>
              ))}
            </Select>
          </div>
          
          <div>
            <Typography variant="small" color="blue-gray" className="mb-1 font-medium">
              Raison du changement (optionnel)
            </Typography>
            <Textarea
              label="Pourquoi souhaitez-vous changer de forfait ?"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              disabled={isLoading}
            />
          </div>
          
          {error && (
            <Alert color="red" icon={<FaTimesCircle className="h-5 w-5" />}>
              {error}
            </Alert>
          )}
          
          {success && (
            <Alert color="green" icon={<FaCheckCircle className="h-5 w-5" />}>
              {success}
            </Alert>
          )}
        </DialogBody>
        <DialogFooter className="space-x-2">
          <Button
            variant="text"
            color="red"
            onClick={onClose}
            disabled={isLoading}
          >
            Annuler
          </Button>
          <Button 
            type="submit" 
            color="blue"
            disabled={isLoading || !newPlan}
            className="flex items-center gap-2"
          >
            {isLoading ? (
              <>
                <Spinner className="h-4 w-4" /> Envoi en cours...
              </>
            ) : (
              'Envoyer la demande'
            )}
          </Button>
        </DialogFooter>
      </form>
    </Dialog>
  );
}

export default ChangeSubscriptionForm;
