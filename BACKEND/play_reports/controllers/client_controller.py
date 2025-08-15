import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from play_reports.serializers.client_serializers import (
    ClientSerializer,
    ClientDetailSerializer,
    ClientUpdateSerializer
)
from play_reports.services.client_service import ClientService

class ClientProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            client = ClientService.get_client_by_user_id(request.user.id)
            serializer = ClientSerializer(client)
            return Response(serializer.data)
        except Client.DoesNotExist:
            return Response({'error': 'Client profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error retrieving client profile for user {request.user.id}: {e}", exc_info=True)
            return Response({'error': 'An error occurred while retrieving the profile.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from django.shortcuts import get_object_or_404
from play_reports.models import Client, RoleClient, Abonnement, TypeAbonnement
from django.contrib.auth import get_user_model

# Get an instance of a logger
logger = logging.getLogger(__name__)

User = get_user_model()

class ClientListController(APIView):
    def get(self, request):
        try:
            role = request.query_params.get('role')
            clients = ClientService.list_clients(role)
            serializer = ClientSerializer(clients, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ClientDetailController(APIView):
    def get(self, request, pk):
        try:
            # Fetch the client using the user ID (pk) from the URL
            client = ClientService.get_client_by_user_id(pk)
            serializer = ClientDetailSerializer(client)
            return Response(serializer.data)
        except Client.DoesNotExist:
            return Response({'error': f'Client with user ID {pk} not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error retrieving client detail for user_id {pk}: {e}", exc_info=True)
            return Response({'error': 'An error occurred while retrieving client details.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ClientUpdateController(APIView):
    def put(self, request, pk):
        try:
            # Fetch the client using the user ID (pk) from the URL
            client = ClientService.get_client_by_user_id(pk)

            # Ensure the authenticated user is the one making the change, or is staff
            if request.user.id != client.user.id and not request.user.is_staff:
                return Response({'error': 'Vous n\'êtes pas autorisé à modifier ce profil.'}, status=status.HTTP_403_FORBIDDEN)

            # Forbid updates for invited members regardless of ownership
            try:
                requester_client = request.user.client_profile
                if requester_client.role_client == RoleClient.MEMBRE_INVITE:
                    return Response({'error': "Les membres invités n'ont pas le droit de modifier le profil."}, status=status.HTTP_403_FORBIDDEN)
            except Client.DoesNotExist:
                pass

            serializer = ClientUpdateSerializer(client, data=request.data, partial=True)
            if serializer.is_valid():
                # Use the client's actual ID for the update
                updated_client = ClientService.update_client(client.id, serializer.validated_data)
                response_serializer = ClientDetailSerializer(updated_client)
                return Response({
                    'message': 'Profil mis à jour avec succès',
                    'data': response_serializer.data
                }, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Client.DoesNotExist:
            return Response({'error': f'Client with user ID {pk} not found.'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error updating client profile for user_id {pk}: {e}", exc_info=True)
            return Response({'error': 'An error occurred while updating the profile.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ClientDeactivateController(APIView):
    def patch(self, request, pk):
        logger.info(f"Attempting to deactivate user with id={pk}")
        try:
            client = get_object_or_404(Client, user_id=pk)
            if request.user.id == pk:
                return Response({'error': 'Vous ne pouvez pas désactiver votre propre compte.'}, status=status.HTTP_403_FORBIDDEN)

            ClientService.set_client_activation_status(client.id, is_active=False)
            logger.info(f"Successfully deactivated client for user_id={pk}")
            return Response({'message': 'Client désactivé avec succès'}, status=status.HTTP_200_OK)
        except Client.DoesNotExist:
            return Response({'error': 'Client non trouvé pour cet utilisateur.'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            logger.error(f"Validation error for user_id={pk}: {e.detail}")
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.critical(f"Unexpected error deactivating user_id={pk}: {e}", exc_info=True)
            return Response({'error': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ClientActivateController(APIView):
    def patch(self, request, pk):
        try:
            client = get_object_or_404(Client, user_id=pk)
            ClientService.set_client_activation_status(client.id, is_active=True)
            return Response({'message': 'Client activé avec succès'}, status=status.HTTP_200_OK)
        except Client.DoesNotExist:
            return Response({'error': 'Client non trouvé pour cet utilisateur.'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ClientChangeAbonnementView(APIView):
    """Change a client's abonnement (per-client) to the requested type.
    Requires staff OR employee with administrator/manage_subscriptions permission.
    POST body: { "type_abonnement": "BASIC|PRO|ENTERPRISE" }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id):
        # Permission checks similar to abonnement_controller.AbonnementDetailView.put
        employee = getattr(request.user, 'employee_profile', None)
        is_allowed = False
        if request.user.is_staff:
            is_allowed = True
        elif employee is not None:
            try:
                is_allowed = employee.is_administrator() or employee.has_permission('manage_subscriptions')
            except Exception:
                is_allowed = False

        if not is_allowed:
            return Response({
                'error': "Accès refusé.",
                'detail': "Vous devez être Administrateur ou disposer de la permission 'manage_subscriptions'."
            }, status=status.HTTP_403_FORBIDDEN)

        type_value = request.data.get('type_abonnement')
        if not type_value:
            return Response({'error': "Le champ 'type_abonnement' est requis."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate choice
        valid_choices = {c[0] for c in TypeAbonnement.choices}
        if type_value not in valid_choices:
            return Response({'error': f"Type d'abonnement invalide. Choix valides: {', '.join(valid_choices)}"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            client = get_object_or_404(Client.objects.select_related('user', 'abonnement'), user_id=user_id)

            # Get or create the target abonnement for that type (active)
            target_abonnement, _ = Abonnement.objects.get_or_create(type_abonnement=type_value, defaults={'is_active': True})

            client.abonnement = target_abonnement
            client.save()

            serializer = ClientDetailSerializer(client)
            return Response({'message': 'Abonnement du client mis à jour avec succès', 'data': serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error changing abonnement for user_id={user_id} to {type_value}: {e}", exc_info=True)
            return Response({'error': 'Une erreur est survenue lors du changement d\'abonnement.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def set_client_status(request, user_id):
    is_active = request.data.get('is_active')
    if is_active is None:
        return Response({'error': 'Le paramètre `is_active` est requis.'}, status=status.HTTP_400_BAD_REQUEST)
    if not isinstance(is_active, bool):
        return Response({'error': 'Le paramètre `is_active` doit être un booléen.'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Prevent an admin from deactivating themselves
    if request.user.id == user_id and not is_active:
        return Response({'error': 'Vous ne pouvez pas désactiver votre propre compte.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        # Find the client associated with the user_id
        client = get_object_or_404(Client, user_id=user_id)
        ClientService.set_client_activation_status(client.id, is_active)
        return Response({'success': f"Le statut de l'utilisateur a été mis à jour."}, status=status.HTTP_200_OK)
    except Client.DoesNotExist:
        return Response({'error': 'Client non trouvé pour cet utilisateur.'}, status=status.HTTP_404_NOT_FOUND)
    except ValidationError as e:
        return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': f'Une erreur est survenue: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)