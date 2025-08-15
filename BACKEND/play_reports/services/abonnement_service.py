import logging
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from rest_framework.exceptions import ValidationError
from play_reports.models import Abonnement, Client, ClientStatus
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
        """Retrieve a list of all subscriptions with their associated clients."""
        return Abonnement.objects.prefetch_related('clients__user').filter(clients__isnull=False).distinct().order_by('-date_creation')

    @staticmethod
    def get_abonnement_by_id(abonnement_id):
        """Retrieve a single subscription by its ID."""
        return get_object_or_404(Abonnement.objects.prefetch_related('clients__user'), id_abonnement=abonnement_id)

    @staticmethod
    def update_abonnement(abonnement_id, data):
        """Update a subscription's details."""
        abonnement = get_object_or_404(Abonnement, id_abonnement=abonnement_id)
        serializer = UpdateAbonnementSerializer(abonnement, data=data, partial=True)
        if serializer.is_valid():
            return serializer.save()
        raise ValidationError(serializer.errors)

    @staticmethod
    def toggle_abonnement_status(abonnement_id):
        """Toggle the active status of a subscription."""
        with transaction.atomic():
            abonnement = get_object_or_404(Abonnement, id_abonnement=abonnement_id)
            abonnement.is_active = not abonnement.is_active
            abonnement.save(update_fields=['is_active'])
            return abonnement
