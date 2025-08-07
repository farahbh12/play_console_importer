# controllers/abonnement_controller.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
import logging
from rest_framework.permissions import AllowAny

from play_reports.models import Abonnement
from play_reports.serializers.abonnement_serializers import (
    AbonnementClientSerializer,
    UpdateAbonnementSerializer,
    ClientAbonnementSerializer
)

logger = logging.getLogger(__name__)

class ClientSubscriptionView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logger.info("Début de la création d'un abonnement client")
        logger.debug(f"Données reçues : {request.data}")
        
        try:
            serializer = ClientAbonnementSerializer(data=request.data)
            if not serializer.is_valid():
                logger.error(f"Erreur de validation : {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info("Validation des données réussie, création en cours...")
            result = serializer.save()
            logger.info("Création réussie")
            
            return Response(result, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.exception("Erreur lors de la création de l'abonnement :")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AbonnementListView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Liste tous les abonnements avec les informations des clients
        GET /abonnements/
        """
        try:
            abonnements = Abonnement.objects.prefetch_related(
                'clients__user'
            ).filter(
                clients__isnull=False
            ).distinct().order_by('-date_creation')
            
            serializer = AbonnementClientSerializer(abonnements, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des abonnements: {str(e)}")
            return Response(
                {'error': 'Erreur lors de la récupération des abonnements'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AbonnementDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, abonnement_id):
        return get_object_or_404(
            Abonnement.objects.prefetch_related('clients__user'),
            id_abonnement=abonnement_id
        )

    def get(self, request, abonnement_id):
        try:
            abonnement = self.get_object(abonnement_id)
            serializer = AbonnementClientSerializer(abonnement)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'abonnement {abonnement_id}: {str(e)}")
            return Response(
                {'error': 'Erreur lors de la récupération de l\'abonnement'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, abonnement_id):
        try:
            abonnement = self.get_object(abonnement_id)
            serializer = UpdateAbonnementSerializer(
                abonnement,
                data=request.data,
                partial=True
            )
            
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            return Response(AbonnementClientSerializer(abonnement).data)
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'abonnement {abonnement_id}: {str(e)}")
            return Response(
                {'error': 'Erreur lors de la mise à jour de l\'abonnement'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AbonnementToggleActiveView(APIView):
    permission_classes = [AllowAny]

    def patch(self, request, abonnement_id):
        try:
            with transaction.atomic():
                abonnement = get_object_or_404(Abonnement, id_abonnement=abonnement_id)
                abonnement.is_active = not abonnement.is_active
                abonnement.save(update_fields=['is_active'])
                
                serializer = AbonnementClientSerializer(abonnement)
                return Response(serializer.data)
                
        except Exception as e:
            logger.error(f"Erreur lors du changement de statut de l'abonnement {abonnement_id}: {str(e)}")
            return Response(
                {'error': 'Erreur lors de la mise à jour du statut'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )