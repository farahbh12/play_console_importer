import logging
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from play_reports.models import Client

# Get an instance of a logger
logger = logging.getLogger(__name__)

User = get_user_model()

class ClientService:
    @staticmethod
    def list_clients(role=None):
        """Retrieve a list of clients, optionally filtered by role."""
        clients = Client.objects.select_related('user').filter(user__isnull=False).all()
        if role:
            clients = clients.filter(role_client=role)
        return clients

    @staticmethod
    def get_client_by_id(client_id):
        """Retrieve a single client by their ID."""
        return get_object_or_404(Client.objects.select_related('user', 'abonnement'), id=client_id)

    @staticmethod
    def get_client_by_user_id(user_id):
        """Récupère un client par l'ID de l'utilisateur associé."""
        return get_object_or_404(Client, user_id=user_id)

    @staticmethod
    def update_client(client_id, validated_data):
        """Update a client's profile information."""
        client = get_object_or_404(Client.objects.select_related('user'), id=client_id)
        user = client.user

        # Update Client fields
        client.first_name = validated_data.get('first_name', client.first_name)
        client.last_name = validated_data.get('last_name', client.last_name)

        # Update User fields
        if 'email' in validated_data and validated_data['email'] != user.email:
            if User.objects.filter(email=validated_data['email']).exclude(pk=user.pk).exists():
                raise ValidationError({'email': 'Un utilisateur avec cet email existe déjà.'})
            user.email = validated_data['email']

        if 'password' in validated_data and validated_data['password']:
            user.set_password(validated_data['password'])

        user.save()
        client.save()
        return client

    @staticmethod
    def set_client_activation_status(client_id, is_active):
        """Activate or deactivate a client's account by their client_id."""
        logger.info(f"Service attempting to set activation status for client_id={client_id} to is_active={is_active}")
        try:
            logger.debug(f"Fetching client with id={client_id}")
            client = Client.objects.select_related('user').get(id=client_id)
            logger.info(f"Found client: {client.id} with user: {client.user}")

            if not client.user:
                logger.warning(f"Client {client.id} has no user. Raising ValidationError.")
                raise ValidationError(f'Client with ID {client_id} has no associated user account.')
            
            user = client.user
            logger.debug(f"Setting user {user.id} is_active status to {is_active}")
            user.is_active = is_active
            user.save()
            logger.info(f"Successfully updated user {user.id} activation status.")
            return user
        except Client.DoesNotExist:
            logger.error(f"Service error: Client with id={client_id} not found. Raising ValidationError.")
            raise ValidationError(f'Client with ID {client_id} not found.')
        except Exception as e:
            logger.critical(f"Unexpected error in service for client_id={client_id}: {e}", exc_info=True)
            raise  # Re-raise the exception to be caught by the controller
