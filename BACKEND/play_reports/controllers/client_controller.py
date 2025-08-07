from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from play_reports.models import Client
from play_reports.serializers.client_serializers import (
    ClientSerializer,
    ClientDetailSerializer,
    ClientUpdateSerializer
)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from django.contrib.auth import get_user_model

User = get_user_model()

class ClientListController(APIView):
    def get(self, request):
        try:
            # Ensure we only get clients with an associated user and pre-fetch the user data.
            clients = Client.objects.select_related('user').filter(user__isnull=False).all()
            role = request.query_params.get('role')
            if role:
                clients = clients.filter(role_client=role)
            serializer = ClientSerializer(clients, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            # Log the error for debugging
            print(f"Error in ClientListController: {e}")
            return Response(
                {'error': 'An unexpected error occurred.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ClientDetailController(APIView):
    def get(self, request, pk):
        try:
            client = get_object_or_404(Client.objects.select_related('user', 'abonnement'), id=pk)
            serializer = ClientDetailSerializer(client)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ClientUpdateController(APIView):
    def put(self, request, pk):
        try:
            client = get_object_or_404(Client.objects.select_related('user'), id=pk)
            serializer = ClientUpdateSerializer(
                instance=client,
                data=request.data,
                partial=True
            )
            
            print(f"[DEBUG] Données reçues pour la mise à jour du client {pk}: {request.data}")

            if not serializer.is_valid():
                print(f"[DEBUG] Erreurs de validation du serializer: {serializer.errors}")
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )

            updated_client = serializer.save()
            response_serializer = ClientDetailSerializer(updated_client)
            
            return Response({
                'message': 'Profil mis à jour avec succès',
                'data': response_serializer.data
            }, status=status.HTTP_200_OK)
            
        except Client.DoesNotExist:
            return Response(
                {'error': 'Client non trouvé.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ClientDeactivateController(APIView):
    def patch(self, request, pk):
        try:
            client = get_object_or_404(Client.objects.select_related('user'), pk=pk)
            client.user.is_active = False
            client.user.save()
            return Response(
                {'message': 'Client désactivé avec succès'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ClientActivateController(APIView):
    def patch(self, request, pk):
        try:
            # Look up the user directly, as the user's status is what we're changing.
            user = get_object_or_404(User, pk=pk)
            user.is_active = True
            user.save()
            return Response(
                {'message': 'Client activé avec succès'},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'Utilisateur non trouvé.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@api_view(['POST'])
@permission_classes([IsAdminUser])
def set_client_status(request, user_id):
    """
    Permet à un administrateur de modifier le statut (actif/inactif) d'un utilisateur.
    """
    try:
        is_active = request.data.get('is_active')
        if is_active is None:
            return Response({'error': 'Le paramètre `is_active` est requis.'}, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(is_active, bool):
            return Response({'error': 'Le paramètre `is_active` doit être un booléen.'}, status=status.HTTP_400_BAD_REQUEST)

        target_user = User.objects.get(pk=user_id)

        # Un administrateur ne peut pas se désactiver lui-même
        if target_user == request.user:
            return Response({'error': 'Vous ne pouvez pas modifier votre propre statut.'}, status=status.HTTP_403_FORBIDDEN)

        target_user.is_active = is_active
        target_user.save()

        return Response({'success': f"Le statut de l'utilisateur {target_user.email} a été mis à jour."}, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({'error': 'Utilisateur non trouvé.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'Une erreur est survenue: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)