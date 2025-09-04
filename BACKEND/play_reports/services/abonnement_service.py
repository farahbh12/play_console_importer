import logging
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from rest_framework.exceptions import ValidationError
from play_reports.models import Abonnement, Client, ClientStatus, TypeAbonnement
from play_reports.serializers.abonnement_serializers import ClientAbonnementSerializer, UpdateAbonnementSerializer
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

class AbonnementService:
    @staticmethod
    @transaction.atomic
    def create_client_subscription(validated_data):
        """Create a new client subscription, user, and client if they don't exist."""
        email = validated_data.get('email')
        nom = validated_data.get('nom')
        prenom = validated_data.get('prenom')
        type_abonnement = validated_data.get('type_abonnement')

        try:
            User = get_user_model()
            user, user_created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'first_name': prenom,
                    'last_name': nom,
                    'is_active': True
                }
            )

            if not user_created:
                update_fields = []
                if user.first_name != prenom:
                    user.first_name = prenom
                    update_fields.append('first_name')
                if user.last_name != nom:
                    user.last_name = nom
                    update_fields.append('last_name')
                if update_fields:
                    user.save(update_fields=update_fields)

            # Règle métier: si le client existe déjà et a un abonnement,
            # il ne peut pas le modifier lui-même. Il doit envoyer une demande.
            existing_client = Client.objects.filter(user=user).first()
            if existing_client and existing_client.abonnement:
                raise ValidationError(
                    {
                        'detail': "Vous avez déjà un abonnement actif. Pour le modifier, veuillez envoyer une demande à l'administrateur.",
                        'code': 'subscription_already_exists'
                    }
                )

            # Créer/récupérer le type d'abonnement demandé
            abonnement, _ = Abonnement.objects.get_or_create(
                type_abonnement=type_abonnement,
                defaults={'is_active': True}
            )

            # Créer ou mettre à jour le client SANS écraser un abonnement existant (déjà géré ci-dessus)
            if existing_client:
                existing_client.first_name = prenom
                existing_client.last_name = nom
                existing_client.abonnement = abonnement
                existing_client.status = ClientStatus.ACTIVE
                existing_client.save(update_fields=['first_name', 'last_name', 'abonnement', 'status'])
                client = existing_client
                client_created = False
            else:
                client = Client.objects.create(
                    user=user,
                    first_name=prenom,
                    last_name=nom,
                    abonnement=abonnement,
                    status=ClientStatus.ACTIVE
                )
                client_created = True

            # Envoi d'email à l'administrateur
            admin_email = 'benhassen.farah@esprit.tn'  # Remplacer par l'email de l'admin
            subject = f'Nouvelle demande d\'abonnement - {prenom} {nom}'
            message = f'''
            Nouvelle demande d'abonnement reçue :
            
            Client: {prenom} {nom}
            Email: {email}
            Type d'abonnement: {type_abonnement}
            
            Connectez-vous à l'administration pour traiter cette demande.
            '''
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[admin_email],
                fail_silently=False,
            )
            
            return {
                'success': True,
                'client_id': client.id,
                'email': user.email,
                'nom': user.last_name,
                'prenom': user.first_name,
                'abonnement_id': abonnement.id_abonnement,
                'abonnement_type': abonnement.get_type_abonnement_display(),
                'is_new_client': client_created,
                'is_new_user': user_created
            }
        except Exception as e:
            logger.exception("Error during subscription creation:")
            raise ValidationError(f"An error occurred during subscription creation: {str(e)}")

    @staticmethod
    def get_abonnement_by_type(type_abonnement):
        """Récupère un abonnement par son type.
        
        Args:
            type_abonnement (str): Le type d'abonnement à récupérer
            
        Returns:
            Abonnement: L'objet Abonnement correspondant
            
        Raises:
            Http404: Si l'abonnement n'existe pas
        """
        from django.http import Http404
        try:
            return Abonnement.objects.get(type_abonnement=type_abonnement, is_active=True)
        except Abonnement.DoesNotExist:
            logger.error(f"Abonnement de type '{type_abonnement}' non trouvé")
            raise Http404(f"Aucun abonnement actif trouvé pour le type: {type_abonnement}")
    
    @staticmethod
    def list_abonnements():
        """
        Récupère la liste de tous les abonnements avec leurs propriétaires.
        """
        from django.db.models import Prefetch
        
        # Récupérer les abonnements avec leurs clients propriétaires
        abonnements = Abonnement.objects.prefetch_related(
            Prefetch(
                'clients',
                queryset=Client.objects.filter(
                    role_client='Owner'
                ).select_related('user'),
                to_attr='owner_clients'
            )
        ).order_by('-date_creation')
        
        # Ne retourner que les abonnements qui ont au moins un propriétaire
        return [abonnement for abonnement in abonnements 
                if hasattr(abonnement, 'owner_clients') and abonnement.owner_clients]
    
    @staticmethod
    def get_abonnement_by_id(abonnement_id):
        """Retrieve a single subscription by its ID."""
        return get_object_or_404(Abonnement.objects.prefetch_related('clients__user'), id_abonnement=abonnement_id)

    @staticmethod
    def update_abonnement(abonnement_id, data):
        """
        Met à jour un abonnement existant.
        La validation des données doit être effectuée par le sérialiseur avant d'appeler cette méthode.
        """
        from django.core.exceptions import ValidationError
        from django.db import transaction
        from play_reports.models import Abonnement, TypeAbonnement
        
        with transaction.atomic():
            # Récupérer l'abonnement existant avec un verrou de ligne
            abonnement = Abonnement.objects.select_for_update().get(id_abonnement=abonnement_id)
            
            # Sauvegarder l'ancien type pour la restauration en cas d'erreur
            old_type = abonnement.type_abonnement
            
            # Vérifier si on essaie de modifier le type d'abonnement
            if 'type_abonnement' in data and data['type_abonnement']:
                new_type = data['type_abonnement']
                
                # Vérifier si le type change réellement (comparaison insensible à la casse)
                if new_type.upper() != old_type.upper():
                    # Vérifier si un autre abonnement avec ce type existe déjà (insensible à la casse)
                    if Abonnement.objects.filter(
                        type_abonnement__iexact=new_type
                    ).exclude(id_abonnement=abonnement_id).exists():
                        # Récupérer le nom d'affichage du type d'abonnement
                        type_display = dict(TypeAbonnement.choices).get(new_type, new_type)
                        raise ValidationError({
                            'type_abonnement': [f"Un abonnement de type '{type_display}' existe déjà."]
                        })
                    
                    # Mettre à jour le type d'abonnement avec la casse exacte du modèle
                    valid_choices = dict(TypeAbonnement.choices)
                    valid_choices_upper = {k.upper(): k for k in valid_choices}
                    correct_case_type = valid_choices_upper.get(new_type.upper(), new_type)
                    abonnement.type_abonnement = correct_case_type
                
                # Supprimer le champ des données pour éviter une double mise à jour
                data.pop('type_abonnement', None)
            
            # Mettre à jour les autres champs
            for field, value in data.items():
                setattr(abonnement, field, value)
            
            try:
                abonnement.full_clean()
                abonnement.save()
                return abonnement
            except Exception as e:
                # En cas d'erreur, restaurer l'ancien type
                abonnement.type_abonnement = old_type
                logger.error(f"Erreur lors de la mise à jour de l'abonnement: {str(e)}")
                if hasattr(e, 'message_dict'):
                    raise ValidationError(e.message_dict)
                if hasattr(e, 'messages'):
                    raise ValidationError({'non_field_errors': e.messages})
                raise ValidationError(str(e))

    @staticmethod
    def toggle_abonnement_status(abonnement_id, active=None):
        """
        Toggle or set the active status of a subscription.
        
        Args:
            abonnement_id: The ID of the subscription to update
            active (bool, optional): If provided, set to this value instead of toggling
            
        Returns:
            Abonnement: The updated subscription object
            
        Raises:
            Http404: If the subscription is not found
            ValidationError: If there's an error updating the subscription
        """
        with transaction.atomic():
            abonnement = get_object_or_404(Abonnement, id_abonnement=abonnement_id)
            
            # If active parameter is provided, set to that value, otherwise toggle
            if active is not None:
                abonnement.is_active = active
            else:
                abonnement.is_active = not abonnement.is_active
                
            abonnement.save(update_fields=['is_active', 'date_mise_a_jour'])
            
            # Log the status change
            status_text = "activé" if abonnement.is_active else "désactivé"
            logger.info(f"Abonnement {abonnement_id} {status_text} avec succès")
            
            return abonnement