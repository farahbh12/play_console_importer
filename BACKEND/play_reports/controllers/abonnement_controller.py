# controllers/abonnement_controller.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
import logging
from django.http import Http404
from django.core.exceptions import ValidationError as DjangoValidationError

from play_reports.models import Client, TypeAbonnement, Abonnement
from play_reports.models.employee import Employee
from play_reports.serializers.abonnement_serializers import (
    AbonnementClientSerializer,
    UpdateAbonnementSerializer,
    ClientAbonnementSerializer
)
from play_reports.services.abonnement_service import AbonnementService
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone

logger = logging.getLogger(__name__)

class ClientSubscriptionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id):
        try:
            from play_reports.models import Client, Abonnement
            
            logger.info(f"Attempting to fetch subscription for client_id: {client_id}")
            
            # Get the client with their subscription
            try:
                client = Client.objects.get(id=client_id)
                logger.info(f"Found client: {client.id}, email: {getattr(client, 'email', 'No email')}")
            except Client.DoesNotExist:
                logger.warning(f"Client with id {client_id} not found")
                return Response(
                    {'error': 'Client non trouvé'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if client has an abonnement
            try:
                subscription = client.abonnement
                if not subscription:
                    logger.warning(f"No subscription found for client {client_id}")
                    return Response(
                        {'error': 'Aucun abonnement trouvé pour ce client'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                logger.info(f"Found subscription for client {client_id}: {subscription}")
                
                return Response({
                    'id': subscription.id_abonnement,
                    'type_abonnement': subscription.type_abonnement,
                    'is_active': subscription.is_active,
                    'date_creation': subscription.date_creation,
                    'date_expiration': getattr(subscription, 'date_expiration', None)
                })
                
            except Abonnement.DoesNotExist:
                logger.warning(f"Subscription not found for client {client_id}")
                return Response(
                    {'error': 'Aucun abonnement trouvé pour ce client'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
        except Exception as e:
            logger.error(f"Error in ClientSubscriptionDetailView: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Une erreur est survenue lors de la récupération de l\'abonnement'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ClientSubscriptionView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ClientAbonnementSerializer(data=request.data)
        if serializer.is_valid():
            try:
                result = AbonnementService.create_client_subscription(serializer.validated_data)
                return Response(result, status=status.HTTP_201_CREATED)
            except ValidationError as e:
                logger.error(f"Validation error during subscription creation: {e.detail}")
                return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.exception("Unexpected error during subscription creation:")
                return Response({'error': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AbonnementListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            # Récupérer les clients propriétaires avec leurs abonnements
            from play_reports.models.client import Client, ClientStatus
            from play_reports.models.abonnement import Abonnement
            
            # Récupérer tous les clients propriétaires actifs avec leurs abonnements
            clients = Client.objects.filter(
                role_client='Owner',
                status=ClientStatus.ACTIVE,
                abonnement__isnull=False
            ).select_related('abonnement', 'user')
            
            # Préparer la liste des résultats
            result = []
            for client in clients:
                user = client.user
                abonnement = client.abonnement
                
                if abonnement:  # S'assurer que l'abonnement existe
                    result.append({
                        'id': abonnement.id_abonnement,  # For frontend compatibility
                        'id_abonnement': abonnement.id_abonnement,  # For backend consistency
                        'type_abonnement': abonnement.type_abonnement,
                        'is_active': abonnement.is_active,
                        'date_creation': abonnement.date_creation.isoformat() if abonnement.date_creation else None,
                        'date_mise_a_jour': abonnement.date_mise_a_jour.isoformat() if abonnement.date_mise_a_jour else None,
                        'first_name': user.first_name if user and user.first_name else client.first_name or '',
                        'last_name': user.last_name if user and user.last_name else client.last_name or 'Non spécifié',
                        'email': user.email if user and user.email else client.email or 'Email non disponible',
                        'user_id': user.id if user else None,
                        'client_id': client.id,
                        'created_at': client.created_at.isoformat() if client.created_at else None,
                        'updated_at': client.updated_at.isoformat() if hasattr(client, 'updated_at') and client.updated_at else None,
                        'status': client.status,
                        'tenant_id': client.tenant_id
                    })
            
            # Trier les résultats par date de création décroissante
            result_sorted = sorted(
                result, 
                key=lambda x: x.get('date_creation') or '', 
                reverse=True
            )
            
            return Response(result_sorted)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des abonnements: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Une erreur est survenue lors de la récupération des abonnements.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AbonnementDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, abonnement_id):
        # Check if the URL is for updating, which should not be accessed with GET
        if 'update' in request.path:
            return Response({'error': 'Method Not Allowed. Use PUT for updates.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        
        try:
            abonnement = AbonnementService.get_abonnement_by_id(abonnement_id)
            serializer = AbonnementClientSerializer(abonnement)
            return Response(serializer.data)
        except Http404:
            return Response({'error': 'Subscription not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error retrieving subscription {abonnement_id}: {e}", exc_info=True)
            return Response({'error': 'An error occurred while retrieving the subscription.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, abonnement_id):
        # Autoriser: Django staff OU Employé Administrateur OU Employé avec la permission 'manage_subscriptions'
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
            return Response(
                {
                    'error': "Accès refusé.",
                    'detail': "Vous devez être Administrateur ou disposer de la permission 'manage_subscriptions'. Sinon, utilisez /api/abonnements/update-request/."
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Ajouter l'ID d'abonnement aux données de la requête pour la validation
        request_data = request.data.copy()
        request_data['id_abonnement'] = abonnement_id
        
        # Valider les données
        serializer = UpdateAbonnementSerializer(data=request_data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            # Mettre à jour l'abonnement avec l'ID fourni
            updated_abonnement = AbonnementService.update_abonnement(abonnement_id, serializer.validated_data)
            response_serializer = AbonnementClientSerializer(updated_abonnement)
            return Response(response_serializer.data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Http404:
            return Response({'error': 'Abonnement non trouvé.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'abonnement {abonnement_id}: {e}", exc_info=True)
            return Response(
                {'error': 'Une erreur est survenue lors de la mise à jour de l\'abonnement.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AbonnementToggleActiveView(APIView):
    """
    Vue pour activer, désactiver ou basculer l'état d'un abonnement.
    """
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        """
        Active, désactive ou bascule l'état d'un abonnement.
        
        Paramètres de requête:
        - action (str, optionnel): 'activate', 'deactivate' ou 'toggle' (par défaut)
        
        Retourne:
        - 200: Abonnement mis à jour avec succès
        - 400: Requête invalide
        - 403: Non autorisé
        - 404: Abonnement non trouvé
        - 500: Erreur serveur
        """
        try:
            # Vérifier que l'ID est valide
            if not pk or not str(pk).isdigit():
                return Response(
                    {'error': 'ID d\'abonnement invalide'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Récupérer l'action depuis les paramètres de requête
            action = request.query_params.get('action', 'toggle').lower()
            
            # Valider l'action
            if action not in ['activate', 'deactivate', 'toggle']:
                return Response(
                    {'error': 'Action non valide. Utilisez \'activate\', \'deactivate\' ou \'toggle\''}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Journaliser la tentative de changement d'état
            logger.info(
                f"Tentative de changement d'état de l'abonnement {pk}. "
                f"Action: {action}, Utilisateur: {request.user.id}"
            )
            
            # Déterminer la valeur de active en fonction de l'action
            active = {
                'activate': True,
                'deactivate': False,
                'toggle': None
            }[action]
            
            # Appeler le service avec la valeur de active appropriée
            abonnement = AbonnementService.toggle_abonnement_status(
                abonnement_id=pk,
                active=active
            )
            
            # Journaliser le succès
            logger.info(
                f"Abonnement {pk} mis à jour avec succès. "
                f"Nouvel état: {'actif' if abonnement.is_active else 'inactif'}"
            )
            
            # Retourner l'abonnement mis à jour
            from ..serializers.abonnement_serializers import AbonnementSerializer
            serializer = AbonnementSerializer(abonnement)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Abonnement.DoesNotExist:
            logger.warning(f"Tentative d'accès à un abonnement inexistant: {pk}")
            return Response(
                {'error': 'Abonnement non trouvé'}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        except ValidationError as e:
            logger.error(
                f"Erreur de validation lors de la mise à jour de l'abonnement {pk}: {e}", 
                exc_info=True
            )
            return Response(
                {'error': str(e.detail) if hasattr(e, 'detail') else str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            logger.error(
                f"Erreur inattendue lors de la mise à jour de l'abonnement {pk}: {e}", 
                exc_info=True
            )
            return Response(
                {'error': 'Une erreur est survenue lors de la mise à jour de l\'abonnement.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AbonnementUpdateRequestView(APIView):
    """
    Vue pour envoyer une demande de changement d'abonnement à l'administrateur
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            # Vérifier si l'utilisateur a un profil client associé
            if not hasattr(request.user, 'client_profile') or not request.user.client_profile:
                return Response(
                    {"error": "Aucun profil client trouvé pour cet utilisateur"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            client = request.user.client_profile
            type_abonnement = request.data.get('type_abonnement')
            
            # Vérifier que le type d'abonnement est fourni
            if not type_abonnement:
                return Response(
                    {"error": "Le type d'abonnement est requis"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Vérifier que le type d'abonnement est valide
            if type_abonnement not in [choice[0] for choice in TypeAbonnement.choices]:
                return Response(
                    {"error": "Type d'abonnement invalide"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Vérifier si l'abonnement demandé est différent de l'abonnement actuel
            if client.abonnement and client.abonnement.type_abonnement == type_abonnement:
                return Response(
                    {"error": "Vous avez déjà cet abonnement"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Envoyer un email à l'administrateur
            admin_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'admin@example.com')
            subject = f'[Demande] Changement d\'abonnement - {client.first_name} {client.last_name}'
            
            context = {
                'client_name': f"{client.first_name} {client.last_name}".strip(),
                'client_email': client.email or request.user.email,
                'ancien_abonnement': client.abonnement.get_type_abonnement_display() if client.abonnement else 'Aucun',
                'nouvel_abonnement': dict(TypeAbonnement.choices).get(type_abonnement, type_abonnement),
                'admin_url': f"{settings.FRONTEND_URL}/admin/" if hasattr(settings, 'FRONTEND_URL') else '#',
                'date_demande': timezone.now().strftime('%d/%m/%Y à %H:%M'),
                'client_id': client.id
            }
            
            # Construire le message sans template (HTML + texte brut)
            html_message = f"""
            <html>
              <body style=\"font-family: Arial, sans-serif; color: #222;\">
                <div style=\"max-width:640px;margin:0 auto;padding:16px;border:1px solid #eee;border-radius:8px;\">
                  <h1 style=\"font-size:20px;margin-bottom:12px;\">Demande de changement d'abonnement</h1>
                  <p>Bonjour l'équipe,</p>
                  <p>
                    Le client ci-dessous a soumis une demande de modification d'abonnement via l'interface.
                    Merci de vérifier et de procéder au changement si la demande est valide.
                  </p>
                  <div style=\"margin:12px 0;padding:12px;background:#f8f9fa;border-radius:6px;\">
                    <p><strong>Client :</strong> {context['client_name']} ({context['client_email']})</p>
                    <p><strong>ID Client :</strong> {context['client_id']}</p>
                    <p><strong>Abonnement actuel :</strong> {context['ancien_abonnement']}</p>
                    <p><strong>Nouvel abonnement demandé :</strong> {context['nouvel_abonnement']}</p>
                    <p><strong>Date de la demande :</strong> {context['date_demande']}</p>
                    {f"<p><strong>Lien admin :</strong> <a href=\\\"{context['admin_url']}\\\" target=\\\"_blank\\\" rel=\\\"noopener\\\">Ouvrir l'administration</a></p>" if context.get('admin_url') else ''}
                  </div>
                  <p>
                    Vous pouvez répondre à ce message ou traiter la demande dans l'interface d'administration.
                  </p>
                  <p style=\"color:#666;font-size:12px;margin-top:16px;\">
                    — Notification automatique • Merci de ne pas répondre à ce message si cela n'est pas nécessaire.
                  </p>
                </div>
              </body>
            </html>
            """
            plain_message = (
                f"Client: {context['client_name']} ({context['client_email']})\n"
                f"ID Client: {context['client_id']}\n"
                f"Abonnement actuel: {context['ancien_abonnement']}\n"
                f"Nouvel abonnement demandé: {context['nouvel_abonnement']}\n"
                f"Date de la demande: {context['date_demande']}\n"
                
            )
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[admin_email],
                html_message=html_message,
                fail_silently=False,
            )
            
            return Response({
                "message": "Votre demande de changement d'abonnement a été envoyée à l'administrateur.",
                "abonnement_demande": {
                    "type": type_abonnement,
                    "nom": context['nouvel_abonnement']
                },
                "abonnement_actuel": {
                    "type": client.abonnement.type_abonnement if client.abonnement else None,
                    "nom": client.abonnement.get_type_abonnement_display() if client.abonnement else 'Aucun'
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur inattendue: {str(e)}", exc_info=True)
            return Response(
                {"error": "Une erreur est survenue lors du traitement de votre demande"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )