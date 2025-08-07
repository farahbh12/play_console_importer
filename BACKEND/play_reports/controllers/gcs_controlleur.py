import  json, logging
from django.apps import apps
from datetime import datetime, timedelta
from datetime import datetime
import os
from asgiref.sync import  async_to_sync
import tempfile
import re
from rest_framework.decorators import api_view 
import logging
from typing import Optional, Dict, List, Tuple, Union, Any
from google.cloud import storage
from google.oauth2 import service_account
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect
from django.http import JsonResponse
from django.db import transaction
from django.conf import settings
from google.cloud import storage
from django.contrib.auth import get_user_model
from play_reports.models.tenant import Tenant
from play_reports.models import Client, RoleClient, DataSource
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication
from play_reports.models.datasource import DataSource

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

import logging
 
from django.utils.dateparse import parse_date
import pandas as pd
from io import StringIO
from django.db import transaction
from django.conf import settings
from play_reports.models import Client
import chardet 
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from google.api_core.exceptions import GoogleAPICallError
from google.cloud.exceptions import NotFound
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from django.utils import timezone
from play_reports.services.gcs_service import gcs_service

logger = logging.getLogger(__name__)
User = get_user_model()
DEBUG = settings.DEBUG





@require_http_methods(["POST"])
@csrf_exempt
def validate_gcs_uri(request):
    try:
        # Récupération des données de la requête (JSON)
        try:
            if request.content_type == 'application/json':

                data = json.loads(request.body)
            else:
                data = request.POST.dict()
                
            email = data.get('email')
            gcs_uri = data.get('uri')
            
            logger.info(f"Données reçues - Email: {email}, URI: {gcs_uri}")
            
        except (json.JSONDecodeError, AttributeError, Exception) as e:
            logger.error(f"Erreur lors de la lecture des données: {str(e)}")
            return JsonResponse(
                {'success': False, 'error': 'Format de données invalide'}, 
                status=400
            )

        # Validation des champs obligatoires
        if not email or not gcs_uri:
            return JsonResponse(
                {'success': False, 'error': 'Email et URI GCS sont obligatoires'},
                status=400
            )

        # Validation du format de l'URI
        if not gcs_uri.startswith("gs://"):
            return JsonResponse(
                {'success': False, 'error': "L'URI GCS doit commencer par 'gs://'"},
                status=400
            )

        # Extraction du nom du bucket
        bucket_name = gcs_uri[5:].split("/")[0]

        # Vérification de l'accès au bucket
        try:
            storage_client = storage.Client()
            bucket = storage_client.get_bucket(bucket_name)
            # Test d'accès en lecture
            list(bucket.list_blobs(max_results=1))
        except NotFound:
            return JsonResponse(
                {'success': False, 'error': f"Le bucket '{bucket_name}' n'existe pas."},
                status=400
            )
        except Forbidden:
            return JsonResponse(
                {'success': False, 'error': f"Accès refusé au bucket '{bucket_name}'. Vérifiez les autorisations."},
                status=403
            )
        except Exception as e:
            logger.error(f"Erreur d'accès au bucket GCS: {str(e)}")
            return JsonResponse(
                {'success': False, 'error': f"Erreur lors de la vérification du bucket GCS: {str(e)}"},
                status=500
            )

        # Vérification de l'utilisateur
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse(
                {'success': False, 'error': "Utilisateur non trouvé."},
                status=404
            )

        # Vérification du rôle du client
        try:
            client = Client.objects.get(user=user, role_client=RoleClient.OWNER)
        except Client.DoesNotExist:
            return JsonResponse(
                {'success': False, 'error': "Seul un client OWNER peut créer un tenant."},
                status=403
            )

        # Vérification si le client a déjà un tenant
        if client.tenant:
            return JsonResponse(
                {'success': False, 'error': "Ce client possède déjà un tenant."},
                status=400
            )

        # Vérification si l'URI est déjà utilisée
        if Tenant.objects.filter(uri=gcs_uri).exists():
            return JsonResponse(
                {'success': False, 'error': "Cette URI GCS est déjà utilisée."},
                status=400
            )

        # Création du tenant
        try:
            with transaction.atomic():
                tenant = Tenant.objects.create(
                    name=f"Tenant-{email.split('@')[0]}",
                    uri=gcs_uri,
                    is_active=True
                )
                
                # Association du tenant au client
                client.tenant = tenant
                client.save()

                # Création de la source de données
                data_source = DataSource.objects.create(
                    tenant=tenant,
                    name=f"Source - {tenant.name}",
                    bucket_uri=gcs_uri,
                    status=DataSource.SyncStatus.PENDING,
                   
                    metadata={
                        'bucket_name': bucket_name,
                        'created_by': user.id,
                        'created_at': timezone.now().isoformat()
                    }
                )

                # Préparation des détails de connexion pour la session
                connection_details = {
                    'gcs_uri': gcs_uri,
                    'email': email,
                    'bucket_name': bucket_name,
                    'access_granted': True,
                    'tenant_id': tenant.id,
                    'tenant_name': tenant.name,
                    'data_source_id': data_source.id,
                    'data_source_name': data_source.name
                }

                # Sauvegarde des détails dans la session
                request.session['gcs_connection_details'] = connection_details
                request.session['validation_success'] = True
                request.session['validation_data'] = connection_details
                request.session.save()

                logger.info(f"Tenant créé avec succès pour l'utilisateur {email}")
                
                # Prépare la réponse de succès avec redirection
                response_data = {
                    'success': True,
                    'redirect': True,
                    'redirect_url': '/validation-success',
                    'message': 'Validation réussie. Redirection...',
                    'data': connection_details
                }
                logger.info(f"Validation réussie pour {email}. Redirection vers /validation-success")
                return JsonResponse(response_data)

        except Exception as e:
            logger.error(f"Erreur lors de la création du tenant: {str(e)}", exc_info=True)
            return JsonResponse(
                {'success': False, 'error': f"Erreur lors de la création du tenant: {str(e)}"},
                status=500
            )

    except Exception as e:
        logger.error(f"Erreur inattendue dans validate_gcs_uri: {str(e)}", exc_info=True)
        return JsonResponse(
            {'success': False, 'error': 'Une erreur inattendue est survenue'},
            status=500
        )


@require_http_methods(["GET"])
def validation_success(request):
    """
    Vue API pour la validation réussie.
    Cette vue est conçue pour fonctionner avec une application React en frontend.
    """
    logger.info("Accès à la vue validation_success")
    
    # Récupération des données depuis la session
    validation_success = request.session.get('validation_success', False)
    validation_data = request.session.get('validation_data', {})
    
    # Préparation des données pour le frontend
    response_data = {
        'success': validation_success,
        'data': {
            'tenant': {
                'id': validation_data.get('tenant_id'),
                'name': validation_data.get('tenant_name', 'Mon Tenant'),
                'uri': validation_data.get('gcs_uri')
            },
            'bucket_name': validation_data.get('bucket_name', 'non spécifié'),
            'email': validation_data.get('email', 'non spécifié'),
            'gcs_uri': validation_data.get('gcs_uri', 'non spécifié'),
            'created_at': validation_data.get('created_at', datetime.now().isoformat())
        }
    }
    
    logger.info(f"Données de validation: {response_data}")
    
    # Si c'est une requête AJAX ou une requête API, on retourne les données en JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
        if not validation_success:
            logger.warning("Aucune validation réussie trouvée dans la session")
            return JsonResponse(
                {'success': False, 'error': 'Aucune validation réussie trouvée'},
                status=400
            )
        return JsonResponse(response_data)
    
    # Nettoyage de la session après utilisation (uniquement si on ne renvoie pas de JSON)
    request.session.pop('validation_success', None)
    request.session.pop('validation_data', None)
    request.session.save()
    
@api_view(['GET'])
@authentication_classes([JWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def get_gcs_sync_status(request):
    try:
        client = Client.objects.select_related('tenant').get(user=request.user)
        if not client.tenant:
            return Response({'success': False, 'error': "Aucun tenant configuré pour ce client."}, status=400)

        gcs_uri = request.query_params.get('gcs_uri') or client.tenant.uri
        if not gcs_uri:
            return Response({'success': False, 'error': "Aucune URI GCS spécifiée ou configurée pour ce tenant."}, status=400)

        try:
            data_source = DataSource.objects.get(tenant=client.tenant, bucket_uri=gcs_uri)
        except DataSource.DoesNotExist:
            return Response({'success': False, 'error': "Aucune source de données trouvée pour cette URI GCS."}, status=404)

        # On retourne le statut et les infos de la dernière synchronisation
        sync_info = {
            'data_source_id': str(data_source.id),
            'data_source_status': data_source.status,
            'last_sync': data_source.last_sync,
            'last_sync_results': data_source.metadata.get('last_sync_results', {}),
            'last_error': data_source.metadata.get('last_error', None)
        }
        return Response({'success': True, 'sync_status': sync_info})

    except Client.DoesNotExist:
        return Response({'success': False, 'error': "Client non trouvé."}, status=404)
    except Exception as e:
        logger.error(f"Erreur get_gcs_sync_status: {e}", exc_info=True)
        return Response({'success': False, 'error': "Erreur interne."}, status=500)

@api_view(['POST'])
@authentication_classes([JWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def trigger_gcs_sync(request):
    try:
        # Récupération du client et du tenant
        client = Client.objects.select_related('tenant').get(user=request.user)
        if not client.tenant:
            return Response(
                {'success': False, 'error': "Aucun tenant configuré pour ce client."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Récupération de l'URI GCS soit depuis les paramètres, soit depuis le tenant
        gcs_uri = request.query_params.get('gcs_uri') or client.tenant.uri
        if not gcs_uri:
            return Response(
                {'success': False, 'error': "Aucune URI GCS spécifiée ou configurée pour ce tenant."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Récupération de la source de données existante ou création
        data_source, created = DataSource.objects.get_or_create(
            tenant=client.tenant,
            bucket_uri=gcs_uri,
            defaults={'status': 'pending', 'metadata': {}}
        )
        
        data_source.status = 'in_progress'
        data_source.save()

        # NOTE: This should ideally be offloaded to a background worker like Celery
        # For now, we run it synchronously in the request.
        try:
            import asyncio
            from play_reports.services.gcs_service import GCSService
            from play_reports.services.process_bucket_service import ProcessBucketService
            
            gcs_service = GCSService()
            processor = ProcessBucketService(
                data_source=data_source,
                gcs_service=gcs_service,
                progress_callback=None
            )

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(processor.process_all(gcs_uri))
            loop.close()
            
            data_source.status = 'completed'
            data_source.last_sync = timezone.now()
            data_source.metadata.update({
                'last_sync_results': {
                    'files_processed': results.get('filesProcessed', 0),
                    'records_inserted': results.get('recordsInserted', 0),
                    'duration_seconds': results.get('duration', 0)
                },
                'last_sync_at': timezone.now().isoformat(),
                'files': results.get('files', [])
            })
            data_source.save()

            return Response({'success': True, 'message': 'Synchronisation terminée avec succès.'})

        except Exception as e:
            data_source.status = 'failed'
            data_source.metadata['last_error'] = {'error': str(e), 'timestamp': timezone.now().isoformat()}
            data_source.save()
            logger.error(f"Erreur lors du traitement: {str(e)}", exc_info=True)
            return Response({'success': False, 'error': f"Erreur lors du traitement: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Client.DoesNotExist:
        return Response({'success': False, 'error': "Client non trouvé."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Erreur inattendue: {str(e)}", exc_info=True)
        return Response({'success': False, 'error': f"Erreur inattendue: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def get_data_source_details(request):
    try:
        client = Client.objects.select_related('tenant').get(user=request.user)
        if not client.tenant or not client.tenant.uri:
            return Response({'success': False, 'error': "Aucun tenant ou URI GCS configuré."}, status=400)

        gcs_uri = client.tenant.uri
        data_source = DataSource.objects.get(tenant=client.tenant, bucket_uri=gcs_uri)
        
        last_sync_results = data_source.metadata.get('last_sync_results', {})
        response_data = {
            'id': str(data_source.id),
            'status': data_source.status,
            'last_sync': data_source.last_sync,
            'files_processed': last_sync_results.get('files_processed', 0),
            'records_inserted': last_sync_results.get('records_inserted', 0),
            'duration_seconds': last_sync_results.get('duration_seconds', 0),
            'last_error': data_source.metadata.get('last_error')
        }
        return Response({'success': True, 'data': response_data})

    except DataSource.DoesNotExist:
        return Response({'success': True, 'data': {'status': 'not_found'}}, status=200)
    except Client.DoesNotExist:
        return Response({'success': False, 'error': "Client non trouvé."}, status=404)
    except Exception as e:
        logger.error(f"Erreur get_data_source_details: {e}", exc_info=True)
        return Response({'success': False, 'error': "Erreur interne."}, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def display_gcs_files(request):
    """
    Display GCS files and their report status for the authenticated user.
    """
    if not request.user.is_authenticated:
        return Response({'success': False, 'error': 'Authentication required.'}, status=401)

    try:
        user = request.user
        # La relation correcte est User -> Client -> Tenant -> DataSource
        client = Client.objects.select_related('tenant').get(user=user)

        if not client.tenant:
            return Response({'success': False, 'error': 'No tenant configured for this user.'}, status=404)

        data_source = DataSource.objects.filter(tenant=client.tenant).first()

        if not data_source or not data_source.bucket_uri:
            return Response({'success': False, 'error': 'No GCS URI configured for this user.'}, status=404)

        # Utiliser async_to_sync pour appeler la fonction asynchrone depuis un contexte synchrone
        files_data = async_to_sync(gcs_service.list_files)(data_source.bucket_uri)
        
        # Extraire les noms de fichiers pour la fonction existante
        file_names = [file['name'] for file in files_data]

        report_statuses = get_report_statuses(file_names)

        return Response({'success': True, 'data': report_statuses})

    except DataSource.DoesNotExist:
        return Response({'success': False, 'error': 'DataSource not found for this user.'}, status=404)
    except Exception as e:
        logger.error(f"Error in display_gcs_files: {e}", exc_info=True)
        return Response({'success': False, 'error': 'An internal server error occurred.'}, status=500)


def get_report_statuses(files_in_bucket):
    REPORT_KEYWORDS = {
        'installs': {'keywords': ['installs', 'overview'], 'display_name': 'Installs'},
        'installs_per_app_version': {'keywords': ['installs', 'appversion'], 'display_name': 'Installs - per App Version'},
        'store_performance': {'keywords': ['storeperformance', 'overview'], 'display_name': 'Store Performance'},
        'reviews': {'keywords': ['reviews'], 'display_name': 'Reviews'},
        'ratings': {'keywords': ['ratings', 'overview'], 'display_name': 'Ratings'},
        'crashes': {'keywords': ['crashes', 'overview'], 'display_name': 'Crashes'},
        'sales_and_earnings': {'keywords': ['sales', 'earnings'], 'display_name': 'Sales and Earnings'},
        'subscriptions': {'keywords': ['subscriptions', 'overview'], 'display_name': 'Subscriptions'},
        'cancellations': {'keywords': ['subscription', 'cancellation'], 'display_name': 'Cancellations'},
        'promotional_content': {'keywords': ['promotionalcontent'], 'display_name': 'Promotional Content'},
    }

    report_status_map = {
        report_type: {
            'name': data['display_name'], 'status': 'n/a', 'last_modified': 'n/a', 'details': 'Report not found.'
        }
        for report_type, data in REPORT_KEYWORDS.items()
    }

    today_str = datetime.now().strftime('%m-%Y')

    for filename in files_in_bucket:
        if not filename.endswith(".csv"): continue
        norm_filename = filename.lower().replace("_", "").replace("-", "")

        matched_report_type = None
        if 'storeperformance' in norm_filename: matched_report_type = 'store_performance'
        elif 'installs' in norm_filename: matched_report_type = 'installs_per_app_version' if 'appversion' in norm_filename else 'installs'
        elif 'reviews' in norm_filename: matched_report_type = 'reviews'
        elif 'ratings' in norm_filename: matched_report_type = 'ratings'
        elif 'crashes' in norm_filename: matched_report_type = 'crashes'
        elif 'sales' in norm_filename or 'earnings' in norm_filename: matched_report_type = 'sales_and_earnings'
        elif 'subscriptions' in norm_filename: matched_report_type = 'cancellations' if 'cancellation' in norm_filename else 'subscriptions'
        elif 'promotionalcontent' in norm_filename: matched_report_type = 'promotional_content'

        if matched_report_type:
            report = report_status_map[matched_report_type]
            report['status'] = 'Ok'
            report['details'] = 'Report ok'
            report['last_modified'] = today_str

    return list(report_status_map.values())