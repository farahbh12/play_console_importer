import logging
import os
import json
import requests
from datetime import datetime, timedelta
from typing import Optional

from django.http import JsonResponse
from django.db.models import Sum, Avg, Count, Q, Max
from django.db.models.functions import TruncMonth
from django.utils.dateparse import parse_date
import asyncio
from play_reports.services.gcs_service import gcs_service
import re

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication

from play_reports.models import (
    Client,
    DataSource,
    google_play_installs_overview,
    google_play_installs_dimensioned,
    google_play_subscriptions_overview,
    google_play_crashes_overview,
    google_play_crashes_dimensioned,
    google_play_ratings_overview,
    google_play_ratings_dimensioned,
    google_play_earnings,
    google_play_store_performance_overview,
    google_play_subscription_cancellation_reasons,
    google_play_buyers_7d_overview,
    google_play_reviews,
)

logger = logging.getLogger(__name__)


# Helpers

def _parse_date(value: Optional[str]) -> Optional[datetime.date]:
    try:
        return parse_date(value) if value else None
    except Exception:
        return None


def _require_params(request, required):
    missing = [p for p in required if not request.query_params.get(p)]
    if missing:
        return Response({
            'success': False,
            'error': f"Missing required params: {', '.join(missing)}"
        }, status=400)
    return None


def _get_default_package_for_tenant(tenant) -> Optional[str]:
    """
    Aggregate distinct package names across overview + dimensioned models and
    return the first available package for the given tenant. Returns None if none found.
    """
    try:
        sources = []
        try:
            sources.append(list(
                google_play_installs_overview.objects.filter(tenant=tenant)
                .values_list('package_name', flat=True).distinct()
            ))
        except Exception:
            pass
        try:
            sources.append(list(
                google_play_installs_dimensioned.objects.filter(tenant=tenant)
                .values_list('package_name', flat=True).distinct()
            ))
        except Exception:
            pass
        try:
            sources.append(list(
                google_play_crashes_overview.objects.filter(tenant=tenant)
                .values_list('package_name', flat=True).distinct()
            ))
        except Exception:
            pass
        try:
            sources.append(list(
                google_play_crashes_dimensioned.objects.filter(tenant=tenant)
                .values_list('package_name', flat=True).distinct()
            ))
        except Exception:
            pass
        try:
            sources.append(list(
                google_play_ratings_overview.objects.filter(tenant=tenant)
                .values_list('package_name', flat=True).distinct()
            ))
        except Exception:
            pass
        try:
            sources.append(list(
                google_play_ratings_dimensioned.objects.filter(tenant=tenant)
                .values_list('package_name', flat=True).distinct()
            ))
        except Exception:
            pass
        try:
            sources.append(list(
                google_play_reviews.objects.filter(tenant=tenant)
                .values_list('package_name', flat=True).distinct()
            ))
        except Exception:
            pass

        collected = []
        for arr in sources:
            for p in (arr or []):
                if p:
                    collected.append(p)
        unique = sorted(set(collected))
        logger.info("default_package: tenant_id=%s unique_count=%s first=%s", getattr(tenant, 'id', None), len(unique), unique[0] if unique else None)
        return unique[0] if unique else None
    except Exception:
        return None


@api_view(['GET'])
@authentication_classes([JWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def packages_list(request):
    """
    GET /api/insights/packages
    Returns the list of distinct package names available for the authenticated client's tenant.
    """
    analysis_type = request.query_params.get('analysis_type', None)
    try:
        client = Client.objects.select_related('tenant').get(user=request.user)
        if not client.tenant:
            return Response({'success': False, 'error': 'No tenant configured.'}, status=400)
        tenant = client.tenant
    except Client.DoesNotExist:
        return Response({'success': False, 'error': 'Client not found.'}, status=404)

    candidates = []
    models_to_check = []
    package_regexes = []

    if analysis_type == 'installs':
        models_to_check.extend([
            google_play_installs_overview,
            google_play_installs_dimensioned
        ])
        package_regexes.append(re.compile(r'stats/installs/installs_([\w\.]+)_\d{6}.*\.csv'))
    elif analysis_type == 'ratings':
        models_to_check.extend([
            google_play_ratings_overview,
            google_play_ratings_dimensioned
        ])
        package_regexes.append(re.compile(r'stats/ratings/ratings_([\w\.]+)_\d{6}.*\.csv'))
    else: # If no type is specified or type is unknown, check all models
        models_to_check.extend([
            google_play_installs_overview, 
            google_play_installs_dimensioned,
            google_play_ratings_overview, 
            google_play_ratings_dimensioned,
            google_play_crashes_overview, 
            google_play_crashes_dimensioned,
            google_play_earnings, 
            google_play_store_performance_overview,
            google_play_subscriptions_overview, 
            google_play_subscription_cancellation_reasons,
        ])
        package_regexes.extend([
            re.compile(r'stats/installs/installs_([\w\.]+)_\d{6}.*\.csv'),
            re.compile(r'stats/ratings/ratings_([\w\.]+)_\d{6}.*\.csv'),
            re.compile(r'reviews/reviews_([\w\.]+)_\d{6}\.csv'),
            re.compile(r'stats/crashes/crashes_([\w\.]+)_\d{6}.*\.csv'),
            re.compile(r'financial-stats/subscriptions/subscriptions_([\w\.]+)_.*\.csv'),
            re.compile(r'stats/store_performance/store_performance_([\w\.]+)_\d{6}.*\.csv')
        ])

    for model in models_to_check:
        try:
            packages = model.objects.filter(tenant=tenant).values_list('package_name', flat=True).distinct()
            candidates.append(list(packages))
        except Exception:
            candidates.append([])

    try:
        data_sources = DataSource.objects.filter(tenant=tenant)
        gcs_packages = set()

        for ds in data_sources:
            if ds.bucket_uri:
                try:
                    # Use async GCS service synchronously
                    files = asyncio.run(gcs_service.list_csv_files(ds.bucket_uri))
                    for f in files:
                        file_name = f.get('name') or ''
                        file_path = file_name
                        for regex in package_regexes:
                            match = regex.search(file_path)
                            if match:
                                gcs_packages.add(match.group(1))
                                break
                except Exception as e:
                    print(f"Error processing bucket {ds.bucket_uri}: {e}")

        candidates.append(list(gcs_packages))
    except Exception as e:
        print(f"Error fetching packages from GCS: {e}")
        candidates.append([])

    all_pkgs = set()
    for arr in candidates:
        for p in arr:
            if p:
                all_pkgs.add(p)

    logger.info("packages_list: total_unique=%s tenant_id=%s", len(all_pkgs), getattr(tenant, 'id', None))

    packages = sorted(all_pkgs)
    return Response({'success': True, 'packages': packages})


@api_view(['GET'])
@authentication_classes([JWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def dimensions_options(request):
    """
    GET /api/insights/dimensions?type=<installs|subscriptions|revenue|crashes|ratings>&package_name=...
    Returns distinct dimension values for the authenticated tenant (and package when relevant).
    """
    analysis_type = request.query_params.get('type')
    package_name = request.query_params.get('package_name')
    if not analysis_type:
        return Response({'success': False, 'error': 'Missing required params: type'}, status=400)

    try:
        client = Client.objects.select_related('tenant').get(user=request.user)
        if not client.tenant:
            return Response({'success': False, 'error': 'No tenant configured.'}, status=400)
        tenant = client.tenant
    except Client.DoesNotExist:
        return Response({'success': False, 'error': 'Client not found.'}, status=404)

    data = {}
    if analysis_type == 'installs':
        qs = google_play_installs_overview.objects.filter(tenant=tenant)
        if package_name:
            qs = qs.filter(package_name=package_name)
        data = {
            'countries': list(qs.values_list('country', flat=True).distinct().order_by('country')),
            'app_versions': list(qs.values_list('app_version', flat=True).distinct().order_by('app_version')),
            'devices': list(qs.values_list('device', flat=True).distinct().order_by('device')),
            'os_versions': list(qs.values_list('os_version', flat=True).distinct().order_by('os_version')),
        }
    elif analysis_type == 'subscriptions':
        qs = google_play_subscriptions_overview.objects.filter(tenant=tenant)
        if package_name:
            qs = qs.filter(package_name=package_name)
        data = {
            'countries': list(qs.values_list('country', flat=True).distinct().order_by('country')),
            'product_ids': list(qs.values_list('product_id', flat=True).distinct().order_by('product_id')),
            'base_plan_ids': list(qs.values_list('base_plan_id', flat=True).distinct().order_by('base_plan_id')),
            'offer_ids': list(qs.values_list('offer_id', flat=True).distinct().order_by('offer_id')),
        }
    elif analysis_type == 'revenue':
        qs = google_play_earnings.objects.filter(tenant=tenant)
        # For revenue, package filtering is done via product_id contains, so we don't filter here
        data = {
            'buyer_countries': list(qs.values_list('buyer_country', flat=True).distinct().order_by('buyer_country')),
            'currencies': list(qs.values_list('merchant_currency', flat=True).distinct().order_by('merchant_currency')),
        }
    elif analysis_type == 'crashes':
        qs = google_play_crashes_overview.objects.filter(tenant=tenant)
        if package_name:
            qs = qs.filter(package_name=package_name)
        data = {
            'app_versions': list(qs.values_list('app_version', flat=True).distinct().order_by('app_version')),
            'devices': list(qs.values_list('device', flat=True).distinct().order_by('device')),
            'os_versions': list(qs.values_list('os_version', flat=True).distinct().order_by('os_version')),
            'android_os_versions': list(qs.values_list('android_os_version', flat=True).distinct().order_by('android_os_version')),
        }
    elif analysis_type == 'ratings':
        qs = google_play_ratings_overview.objects.filter(tenant=tenant)
        if package_name:
            qs = qs.filter(package_name=package_name)
        data = {
            'devices': list(qs.values_list('device', flat=True).distinct().order_by('device')),
        }
    elif analysis_type == 'reviews':
        qs = google_play_reviews.objects.filter(tenant=tenant)
        if package_name:
            qs = qs.filter(package_name=package_name)
        data = {
            'devices': list(qs.values_list('device', flat=True).distinct().order_by('device')),
            'languages': list(qs.values_list('reviewer_language', flat=True).distinct().order_by('reviewer_language')),
            'star_ratings': [1, 2, 3, 4, 5],
        }
    elif analysis_type == 'store_performance':
        qs = google_play_store_performance_overview.objects.filter(tenant=tenant)
        if package_name:
            qs = qs.filter(package_name=package_name)
        data = {
            'countries': list(qs.values_list('country', flat=True).distinct().order_by('country')),
            'traffic_sources': list(qs.values_list('traffic_source', flat=True).distinct().order_by('traffic_source')),
            'search_terms': list(qs.values_list('search_term', flat=True).distinct().order_by('search_term')),
            'utm_sources': list(qs.values_list('utm_source', flat=True).distinct().order_by('utm_source')),
            'utm_campaigns': list(qs.values_list('utm_campaign', flat=True).distinct().order_by('utm_campaign')),
        }
    elif analysis_type == 'cancellations':
        qs = google_play_subscription_cancellation_reasons.objects.filter(tenant=tenant)
        if package_name:
            qs = qs.filter(package_name=package_name)
        data = {
            'countries': list(qs.values_list('country', flat=True).distinct().order_by('country')),
            'cancellation_reasons': list(qs.values_list('cancellation_reason', flat=True).distinct().order_by('cancellation_reason')),
            'cancellation_sub_reasons': list(qs.values_list('cancellation_sub_reason', flat=True).distinct().order_by('cancellation_sub_reason')),
            'subscription_ids': list(qs.values_list('subscription_id', flat=True).distinct().order_by('subscription_id')),
            'sku_ids': list(qs.values_list('sku_id', flat=True).distinct().order_by('sku_id')),
        }
    elif analysis_type == 'buyers7d':
        qs = google_play_buyers_7d_overview.objects.filter(tenant=tenant)
        # buyers7d n'a pas package_name dans le modèle d'overview
        data = {
            'countries': list(qs.values_list('country', flat=True).distinct().order_by('country')),
            'acquisition_channels': list(qs.values_list('acquisition_channel', flat=True).distinct().order_by('acquisition_channel')),
        }
    else:
        return Response({'success': False, 'error': 'Invalid type'}, status=400)

    # Clean out empty/None values
    for k, v in list(data.items()):
        data[k] = [x for x in v if x]

    return Response({'success': True, 'data': data})


@api_view(['GET'])
@authentication_classes([JWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def reviews_insights(request):
    """
    GET /api/insights/reviews?package_name=...&start=YYYY-MM-DD&end=YYYY-MM-DD
    Optionnel: device, rating_min, rating_max, language, limit, offset
    """
    err = _require_params(request, ['start', 'end'])
    if err: return err

    start = _parse_date(request.query_params.get('start'))
    end = _parse_date(request.query_params.get('end'))
    if not start or not end:
        return Response({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

    package_name = request.query_params.get('package_name')
    device = request.query_params.get('device')
    language = request.query_params.get('language')
    rating_min = request.query_params.get('rating_min')
    rating_max = request.query_params.get('rating_max')
    try:
        rating_min = int(rating_min) if rating_min is not None else None
    except Exception:
        rating_min = None
    try:
        rating_max = int(rating_max) if rating_max is not None else None
    except Exception:
        rating_max = None
    try:
        limit = int(request.query_params.get('limit') or 10)
    except Exception:
        limit = 10
    try:
        offset = int(request.query_params.get('offset') or 0)
    except Exception:
        offset = 0

    # Resolve tenant
    try:
        client = Client.objects.select_related('tenant').get(user=request.user)
        if not client.tenant:
            return Response({'success': False, 'error': 'No tenant configured.'}, status=400)
        tenant = client.tenant
    except Client.DoesNotExist:
        return Response({'success': False, 'error': 'Client not found.'}, status=404)

    # If no package provided, infer a default one for this tenant
    if not package_name:
        package_name = _get_default_package_for_tenant(tenant)
        if not package_name:
            return Response({'success': False, 'error': 'No packages found for tenant.'}, status=404)

    qs = google_play_reviews.objects.filter(
        tenant=tenant,
        package_name=package_name,
        review_submit_date__date__gte=start,
        review_submit_date__date__lte=end,
    )
    if device:
        qs = qs.filter(device=device)
    if language:
        qs = qs.filter(reviewer_language=language)
    if rating_min is not None:
        qs = qs.filter(star_rating__gte=rating_min)
    if rating_max is not None:
        qs = qs.filter(star_rating__lte=rating_max)

    # Compute counts/averages explicitly
    # Note: avoid invalid aggregates like Sum(None) which raise OutputFieldIsNoneError
    total_count = qs.count()
    # Average rating over the period
    avg_rating = qs.aggregate(avg=Avg('star_rating')).get('avg')

    # Distribution by stars
    star_breakdown = []
    for s in [5, 4, 3, 2, 1]:
        star_breakdown.append({
            'star': s,
            'count': qs.filter(star_rating=s).count(),
        })

    # Items (paginated)
    items_qs = qs.order_by('-review_submit_date')[offset:offset+limit]
    items = [
        {
            'review_id': r.review_id,
            'date': r.review_submit_date.isoformat(),
            'star_rating': r.star_rating,
            'title': r.review_title,
            'text': r.review_text[:1000] if r.review_text else None,
            'device': r.device,
            'language': r.reviewer_language,
            'developer_reply_date': r.developer_reply_date.isoformat() if r.developer_reply_date else None,
        }
        for r in items_qs
    ]

    data = {
        'package_name': package_name,
        'start': str(start),
        'end': str(end),
        'totals': {
            'reviews_count': total_count,
            'avg_rating': avg_rating,
        },
        'breakdown': star_breakdown,
        'items': items,
        'limit': limit,
        'offset': offset,
    }
    return Response({'success': True, 'data': data})


@api_view(['GET'])
@authentication_classes([JWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def buyers7d_insights(request):
    """
    GET /api/insights/buyers7d?start=YYYY-MM-DD&end=YYYY-MM-DD
    Optionnel: country, acquisition_channel
    Note: ce rapport n'exige pas package_name car le modèle d'overview ne contient pas ce champ.
    """
    err = _require_params(request, ['start', 'end'])
    if err: return err

    start = _parse_date(request.query_params.get('start'))
    end = _parse_date(request.query_params.get('end'))
    if not start or not end:
        return Response({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

    country = request.query_params.get('country')
    acquisition_channel = request.query_params.get('acquisition_channel')

    try:
        client = Client.objects.select_related('tenant').get(user=request.user)
        if not client.tenant:
            return Response({'success': False, 'error': 'No tenant configured.'}, status=400)
        tenant = client.tenant
    except Client.DoesNotExist:
        return Response({'success': False, 'error': 'Client not found.'}, status=404)

    qs = google_play_buyers_7d_overview.objects.filter(
        tenant=tenant,
        date__gte=start,
        date__lte=end,
    )
    if country: qs = qs.filter(country=country)
    if acquisition_channel: qs = qs.filter(acquisition_channel=acquisition_channel)

    agg = qs.aggregate(
        store_listing_visitors=Sum('store_listing_visitors'),
        installers=Sum('installers'),
        buyers=Sum('buyers'),
        repeat_buyers=Sum('repeat_buyers'),
        avg_visitor_to_installer_rate=Avg('visitor_to_installer_rate'),
        avg_installer_to_buyer_rate=Avg('installer_to_buyer_rate'),
        avg_buyer_to_repeat_rate=Avg('buyer_to_repeat_rate'),
    )

    by_channel = list(
        qs.values('acquisition_channel')
          .annotate(buyers=Sum('buyers'))
          .order_by('-buyers')[:5]
    )

    data = {
        'start': str(start),
        'end': str(end),
        'totals': agg,
        'top_channels_by_buyers': by_channel,
    }
    return Response({'success': True, 'data': data})


@api_view(['GET'])
@authentication_classes([JWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def cancellations_insights(request):
    """
    GET /api/insights/cancellations?package_name=...&start=YYYY-MM-DD&end=YYYY-MM-DD
    Optionnel: country, cancellation_reason, cancellation_sub_reason, subscription_id, sku_id
    """
    err = _require_params(request, ['package_name', 'start', 'end'])
    if err: return err

    start = _parse_date(request.query_params.get('start'))
    end = _parse_date(request.query_params.get('end'))
    if not start or not end:
        return Response({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

    package_name = request.query_params.get('package_name')
    country = request.query_params.get('country')
    cancellation_reason = request.query_params.get('cancellation_reason')
    cancellation_sub_reason = request.query_params.get('cancellation_sub_reason')
    subscription_id = request.query_params.get('subscription_id')
    sku_id = request.query_params.get('sku_id')

    try:
        client = Client.objects.select_related('tenant').get(user=request.user)
        if not client.tenant:
            return Response({'success': False, 'error': 'No tenant configured.'}, status=400)
        tenant = client.tenant
    except Client.DoesNotExist:
        return Response({'success': False, 'error': 'Client not found.'}, status=404)

    qs = google_play_subscription_cancellation_reasons.objects.filter(
        tenant=tenant,
        package_name=package_name,
        cancellation_date__gte=start,
        cancellation_date__lte=end,
    )
    if country: qs = qs.filter(country=country)
    if cancellation_reason: qs = qs.filter(cancellation_reason=cancellation_reason)
    if cancellation_sub_reason: qs = qs.filter(cancellation_sub_reason=cancellation_sub_reason)
    if subscription_id: qs = qs.filter(subscription_id=subscription_id)
    if sku_id: qs = qs.filter(sku_id=sku_id)

    agg = qs.aggregate(
        total_cancellations=Sum('cancellation_count'),
    )

    top_reasons = list(
        qs.values('cancellation_reason')
          .annotate(count=Sum('cancellation_count'))
          .order_by('-count')[:5]
    )

    data = {
        'package_name': package_name,
        'start': str(start),
        'end': str(end),
        'totals': agg,
        'top_reasons': top_reasons,
    }
    return Response({'success': True, 'data': data})


@api_view(['GET'])
@authentication_classes([JWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def store_performance_insights(request):
    """
    GET /api/insights/store_performance?package_name=...&start=YYYY-MM-DD&end=YYYY-MM-DD
    Optionnel: country, traffic_source, search_term, utm_source, utm_campaign
    """
    # Validate params
    err = _require_params(request, ['package_name', 'start', 'end'])
    if err: return err

    start = _parse_date(request.query_params.get('start'))
    end = _parse_date(request.query_params.get('end'))
    if not start or not end:
        return Response({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

    package_name = request.query_params.get('package_name')
    country = request.query_params.get('country')
    traffic_source = request.query_params.get('traffic_source')
    search_term = request.query_params.get('search_term')
    utm_source = request.query_params.get('utm_source')
    utm_campaign = request.query_params.get('utm_campaign')

    # Resolve tenant
    try:
        client = Client.objects.select_related('tenant').get(user=request.user)
        if not client.tenant:
            return Response({'success': False, 'error': 'No tenant configured.'}, status=400)
        tenant = client.tenant
    except Client.DoesNotExist:
        return Response({'success': False, 'error': 'Client not found.'}, status=404)

    qs = google_play_store_performance_overview.objects.filter(
        tenant=tenant,
        package_name=package_name,
        date__gte=start,
        date__lte=end,
    )
    if country: qs = qs.filter(country=country)
    if traffic_source: qs = qs.filter(traffic_source=traffic_source)
    if search_term: qs = qs.filter(search_term=search_term)
    if utm_source: qs = qs.filter(utm_source=utm_source)
    if utm_campaign: qs = qs.filter(utm_campaign=utm_campaign)

    agg = qs.aggregate(
        store_listing_visitors=Sum('store_listing_visitors'),
        store_listing_acquisitions=Sum('store_listing_acquisitions'),
        avg_store_listing_conversion_rate=Avg('store_listing_conversion_rate'),
    )

    top_traffic_sources = list(
        qs.values('traffic_source')
          .annotate(visitors=Sum('store_listing_visitors'))
          .order_by('-visitors')[:5]
    )

    data = {
        'package_name': package_name,
        'start': str(start),
        'end': str(end),
        'totals': agg,
        'top_traffic_sources_by_visitors': top_traffic_sources,
    }
    return Response({'success': True, 'data': data})

@api_view(['GET'])
@authentication_classes([JWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def installs_insights(request):
    """
    GET /api/insights/installs?package_name=...&start=YYYY-MM-DD&end=YYYY-MM-DD
    Optionnel: country, app_version, device, os_version
    Le tenant est inféré via l'utilisateur authentifié (Client -> Tenant).
    """
    # Validate params
    err = _require_params(request, ['start', 'end'])
    if err: return err

    start = _parse_date(request.query_params.get('start'))
    end = _parse_date(request.query_params.get('end'))
    if not start or not end:
        return Response({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

    package_name = request.query_params.get('package_name')
    country = request.query_params.get('country')
    app_version = request.query_params.get('app_version')
    device = request.query_params.get('device')
    os_version = request.query_params.get('os_version')

    # Resolve tenant
    try:
        client = Client.objects.select_related('tenant').get(user=request.user)
        if not client.tenant:
            return Response({'success': False, 'error': 'No tenant configured.'}, status=400)
        tenant = client.tenant
    except Client.DoesNotExist:
        return Response({'success': False, 'error': 'Client not found.'}, status=404)

    if not package_name:
        package_name = _get_default_package_for_tenant(tenant)
        if not package_name:
            return Response({'success': False, 'error': 'No packages found for tenant.'}, status=404)

    qs = google_play_installs_overview.objects.filter(
        tenant=tenant,
        package_name=package_name,
        date__gte=start,
        date__lte=end,
    )
    if country: qs = qs.filter(country=country)
    if app_version: qs = qs.filter(app_version=app_version)
    if device: qs = qs.filter(device=device)
    if os_version: qs = qs.filter(os_version=os_version)

    agg = qs.aggregate(
        current_device_installs=Sum('current_device_installs'),
        installs_on_active_devices=Sum('installs_on_active_devices'),
        daily_device_installs=Sum('daily_device_installs'),
        daily_device_uninstalls=Sum('daily_device_uninstalls'),
        daily_device_upgrades=Sum('daily_device_upgrades'),
        total_user_installs=Sum('total_user_installs'),
        daily_user_installs=Sum('daily_user_installs'),
        daily_user_uninstalls=Sum('daily_user_uninstalls'),
    )

    # Net installs
    net_user_installs = (agg.get('daily_user_installs') or 0) - (agg.get('daily_user_uninstalls') or 0)

    # Top countries (if not already filtered)
    top_countries = []
    if not country:
        top_countries = list(
            qs.values('country')
              .annotate(installs=Sum('daily_user_installs'))
              .order_by('-installs')[:5]
        )

    # Additional breakdowns for richer insights
    top_devices = list(
        qs.values('device')
          .annotate(installs=Sum('daily_user_installs'))
          .order_by('-installs')[:5]
    )
    top_os_versions = list(
        qs.values('os_version')
          .annotate(installs=Sum('daily_user_installs'))
          .order_by('-installs')[:5]
    )
    # App versions breakdown (useful to detect anomalies by version)
    top_app_versions = list(
        qs.values('app_version')
          .annotate(installs=Sum('daily_user_installs'))
          .order_by('-installs')[:5]
    )

    data = {
        'package_name': package_name,
        'start': str(start),
        'end': str(end),
        'totals': agg,
        'net_user_installs': net_user_installs,
        'top_countries': top_countries,
        'top_devices_by_installs': top_devices,
        'top_os_versions_by_installs': top_os_versions,
        'top_app_versions_by_installs': top_app_versions,
    }
    return Response({'success': True, 'data': data})


@api_view(['GET'])
@authentication_classes([JWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def ai_analysis(request):
    """
    Generates AI-driven analysis based on installs, ratings, crashes, and reviews data.
    """
    package_name = request.query_params.get('package_name')
    start_str = request.query_params.get('start')
    end_str = request.query_params.get('end')

    if not all([package_name, start_str, end_str]):
        return JsonResponse({'success': False, 'error': 'Package name, start date, and end date are required.'}, status=400)

    try:
        # Date handling
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
        period_days = (end_date - start_date).days + 1
        prev_start_date = start_date - timedelta(days=period_days)
        prev_end_date = start_date - timedelta(days=1)

        # Get tenant from authenticated user
        try:
            client = Client.objects.select_related('tenant').get(user=request.user)
            if not client.tenant:
                return Response({'success': False, 'error': 'No tenant configured.'}, status=400)
            tenant = client.tenant
        except Client.DoesNotExist:
            return Response({'success': False, 'error': 'Client not found.'}, status=404)

        def get_tenant_filtered_queryset(model, date_field='date'):
            """Helper to get tenant-filtered queryset with fallback"""
            qs = model.objects.filter(
                tenant=tenant,
                package_name=package_name,
                **{f'{date_field}__gte': start_date, f'{date_field}__lte': end_date}
            )
            if not qs.exists():
                qs = model.objects.filter(
                    package_name=package_name,
                    **{f'{date_field}__gte': start_date, f'{date_field}__lte': end_date}
                )
            return qs

        # 1. Installations Analysis
        installs_qs = get_tenant_filtered_queryset(google_play_installs_overview)
        installs = installs_qs.aggregate(
            total_installs=Sum('daily_user_installs'),
            total_uninstalls=Sum('daily_user_uninstalls'),
            avg_install_rate=Avg('daily_user_installs'),
            current_installs=Max('current_device_installs')
        )
        
        # 2. Ratings Analysis
        ratings_qs = get_tenant_filtered_queryset(google_play_ratings_overview)
        ratings = ratings_qs.aggregate(
            avg_rating=Avg('daily_average_rating'),
            total_ratings=Count('id'),  # Using count of records as a proxy for total ratings
            avg_rating_delta=Avg('total_average_rating')  # Using total_average_rating as a fallback
        )
        
        # 3. Crashes Analysis
        crashes_qs = get_tenant_filtered_queryset(google_play_crashes_overview)
        crashes = crashes_qs.aggregate(
            total_crashes=Sum('daily_crashes'),
            total_anrs=Sum('daily_anrs'),
            avg_daily_crashes=Avg('daily_crashes')
        )
        
        # 4. Reviews Analysis
        reviews_qs = get_tenant_filtered_queryset(google_play_reviews, 'review_submit_date')
        reviews = reviews_qs.aggregate(
            avg_rating=Avg('star_rating'),
            total_reviews=Count('id'),
            positive_reviews=Count('id', filter=Q(star_rating__gte=4)),
            negative_reviews=Count('id', filter=Q(star_rating__lte=2))
        )
        reviews['sentiment_score'] = (reviews.get('positive_reviews', 0) - reviews.get('negative_reviews', 0)) / max(1, reviews.get('total_reviews', 1))

        # Generate analysis
        analysis = {
            'performance_summary': generate_performance_summary(installs, ratings, crashes, reviews),
            'detailed_description': generate_detailed_description(installs, ratings, crashes, reviews),
            'key_metrics': {
                'installs': installs,
                'ratings': ratings,
                'crashes': crashes,
                'reviews': reviews
            },
            'trends': generate_trends(tenant, package_name, start_date, end_date, prev_start_date, prev_end_date),
            'recommendations': generate_recommendations(installs, ratings, crashes, reviews)
        }

        return JsonResponse({
            'success': True,
            'analysis': analysis
        })

    except Exception as e:
        logger.error(f"AI Analysis error: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f"Analysis failed: {str(e)}"
        }, status=500)

def generate_performance_summary(installs, ratings, crashes, reviews):
    """Generate a high-level performance summary"""
    summary = []
    
    # Install metrics
    net_installs = (installs.get('total_installs') or 0) - (installs.get('total_uninstalls') or 0)
    summary.append(f"📊 Net installations: {net_installs:,} ({(net_installs/max(1, (installs.get('total_installs') or 1))):.1%} of total installs)")
    
    # Rating metrics
    if ratings.get('avg_rating'):
        rating_delta = ratings.get('avg_rating_delta', 0) or 0
        trend = "↑" if rating_delta > 0 else "↓" if rating_delta < 0 else "→"
        summary.append(f"⭐ Average rating: {ratings['avg_rating']:.1f}/5 (from {ratings.get('total_ratings', 0):,} ratings) {trend}")
    
    # Crash metrics
    if crashes.get('avg_daily_crashes'):
        crash_rate = crashes['avg_daily_crashes'] or 0
        status = "⚠️" if crash_rate > 0.05 else "✅"
        summary.append(f"{status} Crash rate: {crash_rate:.2%} ({crashes.get('total_crashes', 0):,} crashes)")
    
    # Review metrics
    if reviews.get('total_reviews', 0) > 0:
        pos_rate = (reviews.get('positive_reviews', 0) or 0) / max(1, reviews.get('total_reviews', 1))
        summary.append(f"💬 User sentiment: {pos_rate:.1%} positive ({reviews['total_reviews']:,} total reviews)")
    
    return summary

def generate_trends(tenant, package_name, start_date, end_date, prev_start_date, prev_end_date):
    """Generate trend analysis compared to previous period"""
    # This is a simplified implementation - you might want to add more sophisticated trend analysis
    return {
        'install_trend': 'stable',  # Implement actual trend calculation
        'rating_trend': 'improving',
        'crash_trend': 'decreasing',
        'review_sentiment_trend': 'improving'
    }

def generate_recommendations(installs, ratings, crashes, reviews):
    """Generate actionable recommendations based on metrics"""
    recommendations = []
    
    # Installation recommendations
    install_rate = installs.get('avg_install_rate', 0) or 0
    if install_rate < 10:
        recommendations.append("📊 Augmentez vos installations : Améliorez votre fiche Play Store avec des captures d'écran attrayantes et une description optimisée.")
    
    # Rating recommendations
    avg_rating = ratings.get('avg_rating', 0) or 0
    if avg_rating < 3.5:
        recommendations.append("⭐ Améliorez vos notes : Analysez les retours utilisateurs et corrigez les problèmes récurrents signalés dans les avis.")
    
    # Crash recommendations
    crash_rate = crashes.get('avg_daily_crashes', 0) or 0
    if crash_rate > 0.05:  # 5% crash rate threshold
        recommendations.append("⚠️ Stabilité à améliorer : Votre application plante trop souvent. Vérifiez les rapports de plantage et corrigez les bogues critiques.")
    
    # Review sentiment recommendations
    if reviews.get('total_reviews', 0) > 0:
        neg_rate = (reviews.get('negative_reviews', 0) or 0) / max(1, reviews.get('total_reviews', 1))
        if neg_rate > 0.2:  # More than 20% negative reviews
            recommendations.append("💬 Répondez aux avis : Beaucoup d'avis négatifs. Répondez aux utilisateurs mécontents et proposez des solutions.")
    
    if not recommendations:
        recommendations = ["✅ Votre application se porte bien ! Continuez à surveiller les métriques clés pour maintenir ces bonnes performances."]
    
    return recommendations

def generate_detailed_description(installs, ratings, crashes, reviews):
    """Génère une description détaillée des performances de l'application"""
    # Installation metrics
    total_installs = installs.get('total_installs', 0) or 0
    install_rate = installs.get('avg_install_rate', 0) or 0
    uninstall_rate = installs.get('uninstall_rate', 0) or 0
    
    # Rating metrics
    avg_rating = ratings.get('avg_rating', 0) or 0
    total_ratings = ratings.get('total_ratings', 0) or 0
    
    # Crash metrics
    crash_rate = crashes.get('avg_daily_crashes', 0) or 0
    total_crashes = crashes.get('total_crashes', 0) or 0
    
    # Review metrics
    total_reviews = reviews.get('total_reviews', 0) or 0
    pos_reviews = reviews.get('positive_reviews', 0) or 0
    neg_reviews = reviews.get('negative_reviews', 0) or 0
    
    # Generate description
    description_parts = []
    
    # Installation analysis
    install_analysis = f"Votre application a été installée {total_installs:,} fois "
    if install_rate > 0:
        install_analysis += f"avec un taux d'installation moyen de {install_rate:.1f}% "
    if uninstall_rate > 0:
        install_analysis += f"et un taux de désinstallation de {uninstall_rate:.1f}%."
    else:
        install_analysis += "avec un très faible taux de désinstallation."
    description_parts.append(install_analysis)
    
    # Rating analysis
    if total_ratings > 0:
        rating_analysis = f"La note moyenne est de {avg_rating:.1f}/5 "
        if avg_rating >= 4.0:
            rating_analysis += "(excellente)"
        elif avg_rating >= 3.0:
            rating_analysis += "(moyenne)"
        else:
            rating_analysis += "(à améliorer)"
        rating_analysis += f" basée sur {total_ratings:,} évaluations."
        description_parts.append(rating_analysis)
    
    # Crash analysis
    if total_crashes > 0:
        crash_analysis = f"Stabilité : "
        if crash_rate <= 0.01:
            crash_analysis += f"Excellente stabilité avec seulement {crash_rate:.1%} de plantages quotidiens."
        elif crash_rate <= 0.05:
            crash_analysis += f"Stabilité moyenne avec {crash_rate:.1%} de plantages quotidiens."
        else:
            crash_analysis += f"Attention : taux de plantage élevé à {crash_rate:.1%} nécessitant une intervention."
        description_parts.append(crash_analysis)
    
    # Review sentiment analysis
    if total_reviews > 0:
        pos_rate = pos_reviews / max(1, total_reviews)
        neg_rate = neg_reviews / max(1, total_reviews)
        
        sentiment_analysis = "Analyse des avis : "
        if pos_rate > 0.7:
            sentiment_analysis += "Très bonnes retours utilisateurs avec une majorité d'avis positifs."
        elif neg_rate > 0.4:
            sentiment_analysis += "Attention : nombreux retours négatifs nécessitant une attention particulière."
        else:
            sentiment_analysis += "Retours utilisateurs mitigés avec une répartition équilibrée d'avis positifs et négatifs."
        description_parts.append(sentiment_analysis)
    
    return " ".join(description_parts)


@api_view(['GET'])
@authentication_classes([JWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def concise_insights(request):
    """
    GET /api/insights/concise?start=YYYY-MM-DD&end=YYYY-MM-DD&package_name=<optional>

    Returns a compact, structured summary combining installs and ratings essentials
    for the authenticated tenant and selected package. Includes deltas vs previous
    period of same length.
    """
    # Validate params
    err = _require_params(request, ['start', 'end'])
    if err:
        return err

    start = _parse_date(request.query_params.get('start'))
    end = _parse_date(request.query_params.get('end'))
    if not start or not end:
        return Response({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

    package_name = request.query_params.get('package_name')

    # Resolve tenant
    try:
        client = Client.objects.select_related('tenant').get(user=request.user)
        if not client.tenant:
            return Response({'success': False, 'error': 'No tenant configured.'}, status=400)
        tenant = client.tenant
    except Client.DoesNotExist:
        return Response({'success': False, 'error': 'Client not found.'}, status=404)

    # Default package if not provided
    if not package_name:
        package_name = _get_default_package_for_tenant(tenant)
        if not package_name:
            return Response({'success': False, 'error': 'No packages found for tenant.'}, status=404)

    # Compute previous period (same length immediately preceding)
    try:
        delta_days = (end - start).days + 1
        prev_end = start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=delta_days - 1)
    except Exception:
        return Response({'success': False, 'error': 'Invalid date range.'}, status=400)

    # Helpers mirroring ai_analysis DB aggregation but returning only essentials
    def build_installs(s_date, e_date):
        qs = google_play_installs_overview.objects.filter(
            tenant=tenant,
            package_name=package_name,
            date__gte=s_date,
            date__lte=e_date,
        )
        if not qs.exists():
            qs = google_play_installs_overview.objects.filter(
                package_name=package_name,
                date__gte=s_date,
                date__lte=e_date,
            )
        agg = qs.aggregate(
            daily_user_installs=Sum('daily_user_installs'),
            daily_user_uninstalls=Sum('daily_user_uninstalls'),
            total_user_installs=Sum('total_user_installs'),
        )
        net = (agg.get('daily_user_installs') or 0) - (agg.get('daily_user_uninstalls') or 0)
        top_countries = list(qs.values('country').annotate(installs=Sum('daily_user_installs')).order_by('-installs')[:5])
        top_devices = list(qs.values('device').annotate(installs=Sum('daily_user_installs')).order_by('-installs')[:5])
        top_os = list(qs.values('os_version').annotate(installs=Sum('daily_user_installs')).order_by('-installs')[:5])
        top_app_versions = list(qs.values('app_version').annotate(installs=Sum('daily_user_installs')).order_by('-installs')[:5])
        return {
            'totals': {
                'daily_user_installs': agg.get('daily_user_installs') or 0,
                'daily_user_uninstalls': agg.get('daily_user_uninstalls') or 0,
                'net_user_installs': net,
                'total_user_installs': agg.get('total_user_installs') or 0,
            },
            'top': {
                'countries': top_countries,
                'devices': top_devices,
                'os_versions': top_os,
                'app_versions': top_app_versions,
            }
        }

    def build_ratings(s_date, e_date):
        qs = google_play_ratings_overview.objects.filter(
            tenant=tenant,
            package_name=package_name,
            date__gte=s_date,
            date__lte=e_date,
        )
        if not qs.exists():
            qs = google_play_ratings_overview.objects.filter(
                package_name=package_name,
                date__gte=s_date,
                date__lte=e_date,
            )
        agg = qs.aggregate(
            daily_avg=Avg('daily_average_rating'),
            total_avg=Avg('total_average_rating'),
        )
        top_devices = list(qs.values('device').annotate(avg_rating=Avg('daily_average_rating')).order_by('-avg_rating')[:5])
        return {
            'averages': {
                'daily_avg': agg.get('daily_avg'),
                'total_avg': agg.get('total_avg'),
            },
            'top': {
                'devices_by_avg_rating': top_devices,
            }
        }

    curr_i = build_installs(start, end)
    curr_r = build_ratings(start, end)
    prev_i = build_installs(prev_start, prev_end)
    prev_r = build_ratings(prev_start, prev_end)

    # Deltas
    deltas_installs = {
        'daily_user_installs': (curr_i['totals']['daily_user_installs'] or 0) - (prev_i['totals']['daily_user_installs'] or 0),
        'daily_user_uninstalls': (curr_i['totals']['daily_user_uninstalls'] or 0) - (prev_i['totals']['daily_user_uninstalls'] or 0),
        'net_user_installs': (curr_i['totals']['net_user_installs'] or 0) - (prev_i['totals']['net_user_installs'] or 0),
    }
    curr_daily_avg = curr_r['averages']['daily_avg'] if curr_r['averages']['daily_avg'] is not None else 0
    prev_daily_avg = prev_r['averages']['daily_avg'] if prev_r['averages']['daily_avg'] is not None else 0
    curr_total_avg = curr_r['averages']['total_avg'] if curr_r['averages']['total_avg'] is not None else 0
    prev_total_avg = prev_r['averages']['total_avg'] if prev_r['averages']['total_avg'] is not None else 0
    deltas_ratings = {
        'daily_avg': curr_daily_avg - prev_daily_avg,
        'total_avg': curr_total_avg - prev_total_avg,
    }

    payload = {
        'package_name': package_name,
        'period': {
            'start': str(start),
            'end': str(end),
            'previous_start': str(prev_start),
            'previous_end': str(prev_end),
        },
        'installs': {
            **curr_i,
            'deltas': deltas_installs,
        },
        'ratings': {
            **curr_r,
            'deltas': deltas_ratings,
        }
    }

    return JsonResponse({'success': True, 'data': payload})

@api_view(['GET'])
@authentication_classes([JWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def installs_monthly_analysis(request):
    """
    GET /api/insights/installs/monthly?start=YYYY-MM-DD&end=YYYY-MM-DD&package_name=<optional>

    Monthly aggregation for installs based on:
    - google_play_installs_overview: daily_user_installs (totals per month), app_version breakdown
    - google_play_installs_dimensioned: carrier breakdown

    Returns:
    { success: true, months: [ { month, totals: { daily_user_installs }, top: { app_versions: [], carriers: [] } } ] }
    """
    err = _require_params(request, ['start', 'end'])
    if err: return err

    start = _parse_date(request.query_params.get('start'))
    end = _parse_date(request.query_params.get('end'))
    if not start or not end:
        return Response({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

    package_name = request.query_params.get('package_name')

    # Resolve tenant
    try:
        client = Client.objects.select_related('tenant').get(user=request.user)
        if not client.tenant:
            return Response({'success': False, 'error': 'No tenant configured.'}, status=400)
        tenant = client.tenant
    except Client.DoesNotExist:
        return Response({'success': False, 'error': 'Client not found.'}, status=404)

    # Default package if missing; if none found, return empty months
    if not package_name:
        package_name = _get_default_package_for_tenant(tenant)
        if not package_name:
            return JsonResponse({'success': True, 'months': []})

    # Overview
    io_qs = google_play_installs_overview.objects.filter(
        tenant=tenant,
        package_name=package_name,
        date__gte=start,
        date__lte=end,
    )
    if not io_qs.exists():
        io_qs = google_play_installs_overview.objects.filter(
            package_name=package_name,
            date__gte=start,
            date__lte=end,
        )
    io_monthly = list(
        io_qs.annotate(month=TruncMonth('date'))
            .values('month')
            .annotate(daily_user_installs=Sum('daily_user_installs'))
            .order_by('month')
    )
    io_appv = list(
        io_qs.exclude(app_version__isnull=True).exclude(app_version='')
            .annotate(month=TruncMonth('date'))
            .values('month', 'app_version')
            .annotate(daily_user_installs=Sum('daily_user_installs'))
            .order_by('month', '-daily_user_installs')
    )

    # Dimensioned (carrier)
    id_qs = google_play_installs_dimensioned.objects.filter(
        tenant=tenant,
        package_name=package_name,
        date__gte=start,
        date__lte=end,
    )
    if not id_qs.exists():
        id_qs = google_play_installs_dimensioned.objects.filter(
            package_name=package_name,
            date__gte=start,
            date__lte=end,
        )
    id_carrier = list(
        id_qs.exclude(carrier__isnull=True).exclude(carrier='')
            .annotate(month=TruncMonth('date'))
            .values('month', 'carrier')
            .annotate(daily_user_installs=Sum('daily_user_installs'))
            .order_by('month', '-daily_user_installs')
    )

    # Build months structure
    from collections import defaultdict
    month_key = lambda d: (d['month'].strftime('%Y-%m-01') if hasattr(d['month'], 'strftime') else str(d['month']))

    installs_map = defaultdict(lambda: {
        'totals': {'daily_user_installs': 0},
        'top': {'app_versions': [], 'carriers': []}
    })

    for row in io_monthly:
        mk = month_key(row)
        installs_map[mk]['totals']['daily_user_installs'] = row.get('daily_user_installs') or 0

    for row in io_appv:
        mk = month_key(row)
        installs_map[mk]['top']['app_versions'].append({
            'app_version': row['app_version'],
            'daily_user_installs': row.get('daily_user_installs') or 0,
        })

    for row in id_carrier:
        mk = month_key(row)
        installs_map[mk]['top']['carriers'].append({
            'carrier': row['carrier'],
            'daily_user_installs': row.get('daily_user_installs') or 0,
        })

    # Sort and cap
    for mk, data in installs_map.items():
        data['top']['app_versions'] = sorted(
            data['top']['app_versions'], key=lambda x: x['daily_user_installs'], reverse=True
        )[:5]
        data['top']['carriers'] = sorted(
            data['top']['carriers'], key=lambda x: x['daily_user_installs'], reverse=True
        )[:5]

    # Debug logging
    try:
        logger.info(
            "installs_monthly_analysis params tenant_id=%s package=%s start=%s end=%s io_exists=%s id_exists=%s",
            getattr(tenant, 'id', None), package_name, start, end, io_qs.exists(), id_qs.exists()
        )
        logger.info(
            "installs_monthly_analysis counts io=%s id=%s io_monthly_rows=%s io_appv_rows=%s id_carrier_rows=%s",
            io_qs.count(), id_qs.count(), len(io_monthly), len(io_appv), len(id_carrier)
        )
    except Exception:
        pass

    months = [ {'month': mk, **installs_map[mk]} for mk in sorted(installs_map.keys()) ]
    logger.info("installs_monthly_analysis months_len=%s", len(months))
    return JsonResponse({'success': True, 'months': months})


@api_view(['GET'])
@authentication_classes([JWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def ratings_monthly_analysis(request):
    """
    GET /api/insights/ratings/monthly?start=YYYY-MM-DD&end=YYYY-MM-DD&package_name=<optional>

    Monthly aggregation for ratings based on:
    - google_play_ratings_overview: daily_average_rating, total_average_rating
    - google_play_ratings_dimensioned: device, language, country breakdowns

    Returns:
    { success: true, months: [ { month, averages: { daily_avg, total_avg }, top: { devices: [], languages: [], countries: [] } } ] }
    """
    err = _require_params(request, ['start', 'end'])
    if err: return err

    start = _parse_date(request.query_params.get('start'))
    end = _parse_date(request.query_params.get('end'))
    if not start or not end:
        return Response({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

    package_name = request.query_params.get('package_name')

    # Resolve tenant
    try:
        client = Client.objects.select_related('tenant').get(user=request.user)
        if not client.tenant:
            return Response({'success': False, 'error': 'No tenant configured.'}, status=400)
        tenant = client.tenant
    except Client.DoesNotExist:
        return Response({'success': False, 'error': 'Client not found.'}, status=404)

    # Default package if missing; if none found, return empty months
    if not package_name:
        package_name = _get_default_package_for_tenant(tenant)
        if not package_name:
            return JsonResponse({'success': True, 'months': []})

    # Overview
    ro_qs = google_play_ratings_overview.objects.filter(
        tenant=tenant,
        package_name=package_name,
        date__gte=start,
        date__lte=end,
    )
    if not ro_qs.exists():
        ro_qs = google_play_ratings_overview.objects.filter(
            package_name=package_name,
            date__gte=start,
            date__lte=end,
        )
    ro_monthly = list(
        ro_qs.annotate(month=TruncMonth('date'))
            .values('month')
            .annotate(
                daily_avg=Avg('daily_average_rating'),
                total_avg=Avg('total_average_rating'),
            )
            .order_by('month')
    )

    # Dimensioned breakdowns
    rd_qs = google_play_ratings_dimensioned.objects.filter(
        tenant=tenant,
        package_name=package_name,
        date__gte=start,
        date__lte=end,
    )
    if not rd_qs.exists():
        rd_qs = google_play_ratings_dimensioned.objects.filter(
            package_name=package_name,
            date__gte=start,
            date__lte=end,
        )

    def dim_avg(qs, field):
        return list(
            qs.exclude(**{f"{field}__isnull": True}).exclude(**{field: ''})
              .annotate(month=TruncMonth('date'))
              .values('month', field)
              .annotate(avg_rating=Avg('daily_average_rating'))
              .order_by('month', '-avg_rating')
        )

    rd_device = dim_avg(rd_qs, 'device')
    rd_language = dim_avg(rd_qs, 'language')
    rd_country = dim_avg(rd_qs, 'country')

    from collections import defaultdict
    month_key = lambda d: (d['month'].strftime('%Y-%m-01') if hasattr(d['month'], 'strftime') else str(d['month']))

    ratings_map = defaultdict(lambda: {
        'averages': {'daily_avg': None, 'total_avg': None},
        'top': {
            'devices': [],
            'languages': [],
            'countries': [],
        }
    })

    for row in ro_monthly:
        mk = month_key(row)
        ratings_map[mk]['averages']['daily_avg'] = row.get('daily_avg')
        ratings_map[mk]['averages']['total_avg'] = row.get('total_avg')

    def push(rows, field, key):
        for r in rows:
            mk = month_key(r)
            ratings_map[mk]['top'][key].append({
                field: r[field],
                'avg_rating': r.get('avg_rating'),
            })

    push(rd_device, 'device', 'devices')
    push(rd_language, 'language', 'languages')
    push(rd_country, 'country', 'countries')

    # Sort top 5 by daily_average_rating
    for mk, data in ratings_map.items():
        for key in ['devices', 'languages', 'countries']:
            # Sort and cap, ensuring avg_rating is not None
            sorted_list = sorted(
                [x for x in data['top'][key] if x.get('avg_rating') is not None],
                key=lambda x: x['avg_rating'], reverse=True
            )
            data['top'][key] = sorted_list[:3]

    # Debug logging
    logger.info(
        "ratings_monthly_analysis params tenant_id=%s package=%s start=%s end=%s ro_exists=%s rd_exists=%s",
        getattr(tenant, 'id', None), package_name, start, end, ro_qs.exists(), rd_qs.exists()
    )
    logger.info(
        "ratings_monthly_analysis counts ro=%s rd=%s ro_monthly_rows=%s rd_device_rows=%s rd_language_rows=%s rd_country_rows=%s",
        ro_qs.count(), rd_qs.count(), len(ro_monthly), len(rd_device), len(rd_language), len(rd_country)
    )

    months = [ {'month': mk, **ratings_map[mk]} for mk in sorted(ratings_map.keys()) ]
    logger.info("ratings_monthly_analysis months_len=%s", len(months))
    return JsonResponse({'success': True, 'months': months})

@api_view(['GET'])
@authentication_classes([JWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def monthly_insights(request):
    """
    GET /api/insights/monthly?start=YYYY-MM-DD&end=YYYY-MM-DD&package_name=<optional>

    Retourne des agrégations PAR MOIS pour:
    - Installs (overview): daily_user_installs
      + Découpage par app_version (overview) et carrier (dimensioned)
    - Ratings (overview): daily_average_rating, total_average_rating
      + Découpage par device, language, country (dimensioned)
    """
    err = _require_params(request, ['start', 'end'])
    if err: return err

    start = _parse_date(request.query_params.get('start'))
    end = _parse_date(request.query_params.get('end'))
    if not start or not end:
        return Response({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

    package_name = request.query_params.get('package_name')

    # Resolve tenant
    try:
        client = Client.objects.select_related('tenant').get(user=request.user)
        if not client.tenant:
            return Response({'success': False, 'error': 'No tenant configured.'}, status=400)
        tenant = client.tenant
    except Client.DoesNotExist:
        return Response({'success': False, 'error': 'Client not found.'}, status=404)

    # Default package if missing
    if not package_name:
        package_name = _get_default_package_for_tenant(tenant)
        if not package_name:
            return Response({'success': False, 'error': 'No packages found for tenant.'}, status=404)

    # -------- INSTalls: overview per month + app_version breakdown (overview)
    io_qs = google_play_installs_overview.objects.filter(
        tenant=tenant,
        package_name=package_name,
        date__gte=start,
        date__lte=end,
    )
    # Fallback sans tenant si besoin (legacy)
    if not io_qs.exists():
        io_qs = google_play_installs_overview.objects.filter(
            package_name=package_name,
            date__gte=start,
            date__lte=end,
        )

    io_monthly = list(
        io_qs.annotate(month=TruncMonth('date'))
            .values('month')
            .annotate(daily_user_installs=Sum('daily_user_installs'))
            .order_by('month')
    )

    io_appv = list(
        io_qs.exclude(app_version__isnull=True).exclude(app_version='')
            .annotate(month=TruncMonth('date'))
            .values('month', 'app_version')
            .annotate(daily_user_installs=Sum('daily_user_installs'))
            .order_by('month', '-daily_user_installs')
    )

    # Carrier breakdown from DIMENSIONED per month
    id_qs = google_play_installs_dimensioned.objects.filter(
        tenant=tenant,
        package_name=package_name,
        date__gte=start,
        date__lte=end,
    )
    if not id_qs.exists():
        id_qs = google_play_installs_dimensioned.objects.filter(
            package_name=package_name,
            date__gte=start,
            date__lte=end,
        )
    id_carrier = list(
        id_qs.exclude(carrier__isnull=True).exclude(carrier='')
            .annotate(month=TruncMonth('date'))
            .values('month', 'carrier')
            .annotate(daily_user_installs=Sum('daily_user_installs'))
            .order_by('month', '-daily_user_installs')
    )

    # -------- RATINGS: overview per month + device/language/country breakdowns (dimensioned)
    ro_qs = google_play_ratings_overview.objects.filter(
        tenant=tenant,
        package_name=package_name,
        date__gte=start,
        date__lte=end,
    )
    if not ro_qs.exists():
        ro_qs = google_play_ratings_overview.objects.filter(
            package_name=package_name,
            date__gte=start,
            date__lte=end,
        )
    ro_monthly = list(
        ro_qs.annotate(month=TruncMonth('date'))
            .values('month')
            .annotate(
                daily_average_rating=Avg('daily_average_rating'),
                total_average_rating=Avg('total_average_rating'),
            )
            .order_by('month')
    )

    rd_qs = google_play_ratings_dimensioned.objects.filter(
        tenant=tenant,
        package_name=package_name,
        date__gte=start,
        date__lte=end,
    )
    if not rd_qs.exists():
        rd_qs = google_play_ratings_dimensioned.objects.filter(
            package_name=package_name,
            date__gte=start,
            date__lte=end,
        )

    def dim_avg(qs, field):
        return list(
            qs.exclude(**{f"{field}__isnull": True}).exclude(**{field: ''})
              .annotate(month=TruncMonth('date'))
              .values('month', field)
              .annotate(daily_average_rating=Avg('daily_average_rating'))
              .order_by('month', '-daily_average_rating')
        )

    rd_device = dim_avg(rd_qs, 'device')
    rd_language = dim_avg(rd_qs, 'language')
    rd_country = dim_avg(rd_qs, 'country')

    # Structure par mois, avec top-N (ex: top 5) par mois pour les breakdowns
    from collections import defaultdict
    month_key = lambda d: (d['month'].strftime('%Y-%m-01') if hasattr(d['month'], 'strftime') else str(d['month']))

    # Installs: build map month -> aggregates and breakdowns
    installs_months = defaultdict(lambda: {
        'totals': {'daily_user_installs': 0},
        'breakdowns': {'app_version': [], 'carrier': []}
    })
    for row in io_monthly:
        mk = month_key(row)
        installs_months[mk]['totals']['daily_user_installs'] = row.get('daily_user_installs') or 0
    # app_version breakdown top 5 per month
    for row in io_appv:
        mk = month_key(row)
        installs_months[mk]['breakdowns']['app_version'].append({
            'app_version': row['app_version'],
            'daily_user_installs': row.get('daily_user_installs') or 0,
        })
    # carrier breakdown top 5 per month
    for row in id_carrier:
        mk = month_key(row)
        installs_months[mk]['breakdowns']['carrier'].append({
            'carrier': row['carrier'],
            'daily_user_installs': row.get('daily_user_installs') or 0,
        })

    # Sort and cap top lists
    for mk, data in installs_months.items():
        data['breakdowns']['app_version'] = sorted(
            data['breakdowns']['app_version'], key=lambda x: x['daily_user_installs'], reverse=True
        )[:5]
        data['breakdowns']['carrier'] = sorted(
            data['breakdowns']['carrier'], key=lambda x: x['daily_user_installs'], reverse=True
        )[:5]

    # Ratings: build map month -> aggregates and breakdowns
    ratings_months = defaultdict(lambda: {
        'averages': {'daily_average_rating': None, 'total_average_rating': None},
        'breakdowns': {'device': [], 'language': [], 'country': []}
    })
    for row in ro_monthly:
        mk = month_key(row)
        ratings_months[mk]['averages']['daily_average_rating'] = row.get('daily_avg')
        ratings_months[mk]['averages']['total_average_rating'] = row.get('total_avg')

    def push_dim(rows, field, target_key):
        for r in rows:
            mk = month_key(r)
            ratings_months[mk]['breakdowns'][target_key].append({
                target_key: r[field],
                'daily_average_rating': r.get('daily_average_rating'),
            })

    push_dim(rd_device, 'device', 'device')
    push_dim(rd_language, 'language', 'language')
    push_dim(rd_country, 'country', 'country')

    # Sort top 5 by daily_average_rating
    for mk, data in ratings_months.items():
        for key in ['device', 'language', 'country']:
            # Sort and cap, ensuring avg_rating is not None
            sorted_list = sorted(
                [x for x in data['breakdowns'][key] if x.get('daily_average_rating') is not None],
                key=lambda x: x['daily_average_rating'], reverse=True
            )
            data['breakdowns'][key] = sorted_list[:3]

    # Build ordered month list union of both sides
    all_months = sorted(set(list(installs_months.keys()) + list(ratings_months.keys())))
    installs_series = []
    ratings_series = []
    for mk in all_months:
        if mk in installs_months:
            installs_series.append({'month': mk, **installs_months[mk]})
        if mk in ratings_months:
            ratings_series.append({'month': mk, **ratings_months[mk]})

    payload = {
        'package_name': package_name,
        'period': {
            'start': str(start),
            'end': str(end),
        },
        'installs': {
            'monthly': installs_series,
            'metric': 'daily_user_installs',
            'breakdowns': ['app_version', 'carrier']
        },
        'ratings': {
            'monthly': ratings_series,
            'metrics': ['daily_average_rating', 'total_average_rating'],
            'breakdowns': ['device', 'language', 'country']
        }
    }

    return JsonResponse({'success': True, 'data': payload})

@api_view(['GET'])
@authentication_classes([JWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def ai_analysis_installs(request):
    package_name = request.query_params.get('package_name')
    start_date = request.query_params.get('start')
    end_date = request.query_params.get('end')

    if not all([package_name, start_date, end_date]):
        return JsonResponse({'success': False, 'error': 'Paramètres package_name, start, et end sont requis.'}, status=400)

    try:
        base_url = request.build_absolute_uri('/')[:-1]
        auth_header = {'Authorization': request.headers.get('Authorization')}
        installs_url = f"{base_url}/api/insights/installs?package_name={package_name}&start={start_date}&end={end_date}"
        installs_response = requests.get(installs_url, headers=auth_header, timeout=30)
        installs_response.raise_for_status()
        installs_data = installs_response.json().get('data', {})

        installs_totals = installs_data.get('totals', {})
        prompt = (
            f"Analyse pour un client (langage simple, clair et direct) les données d'installation suivantes pour l'application '{package_name}' "
            f"entre {start_date} et {end_date}. "
            f"Objectif: fournir un résumé exécutif avec (1) points forts, (2) points faibles, et (3) recommandations concrètes sur les installations.\n\n"
            f"**Données d'installation :**\n"
            f"- Installations totales: {installs_totals.get('daily_user_installs', 0)}\n"
            f"- Désinstallations: {installs_totals.get('daily_user_uninstalls', 0)}\n"
            f"- Installations nettes: {installs_data.get('net_user_installs', 0)}\n\n"
            f"Structure de la réponse attendue :\n"
            f"1. **Bilan général des installations** (1-2 phrases)\n"
            f"2. **Points forts** (2-3 points max)\n"
            f"3. **Points faibles** (2-3 points max)\n"
            f"4. **Recommandations** (2-3 actions concrètes et priorisées)"
        )

        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not openai_api_key:
            return JsonResponse({'success': False, 'error': 'OPENAI_API_KEY non configurée sur le serveur.'}, status=500)

        headers = {
            'Authorization': f'Bearer {openai_api_key}',
            'Content-Type': 'application/json',
        }
        payload = {
            'model': 'gpt-3.5-turbo',
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.7,
            'max_tokens': 400,
        }
        
        try:
            openai_response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=payload, timeout=60)
            openai_response.raise_for_status()
            analysis_result = openai_response.json()['choices'][0]['message']['content']
            
            return JsonResponse({'success': True, 'data': {'analysis': analysis_result.strip()}})
        
        except requests.exceptions.RequestException as e:
            return JsonResponse({'success': False, 'error': f"Erreur de communication avec l'API OpenAI: {e}"}, status=502)

    except requests.exceptions.RequestException as e:
        return JsonResponse({'success': False, 'error': f"Erreur lors de la récupération des données internes: {e}"}, status=500)
    except Exception as e:
        logger.error(f"[ai_analysis_installs] Erreur inattendue: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': 'Une erreur inattendue est survenue.'}, status=500)

@api_view(['GET'])
@authentication_classes([JWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def ai_analysis_ratings(request):
    package_name = request.query_params.get('package_name')
    start_date = request.query_params.get('start')
    end_date = request.query_params.get('end')

    if not all([package_name, start_date, end_date]):
        return JsonResponse({'success': False, 'error': 'Paramètres package_name, start, et end sont requis.'}, status=400)

    try:
        base_url = request.build_absolute_uri('/')[:-1]
        auth_header = {'Authorization': request.headers.get('Authorization')}
        ratings_url = f"{base_url}/api/insights/ratings?package_name={package_name}&start={start_date}&end={end_date}"
        ratings_response = requests.get(ratings_url, headers=auth_header, timeout=30)
        ratings_response.raise_for_status()
        ratings_data = ratings_response.json().get('data', {})

        ratings_averages = ratings_data.get('averages', {})
        prompt = (
            f"Analyse pour un client (langage simple, clair et direct) les données de notations suivantes pour l'application '{package_name}' "
            f"entre {start_date} et {end_date}. "
            f"Objectif: fournir un résumé exécutif avec (1) points forts, (2) points faibles, et (3) recommandations concrètes sur les notations.\n\n"
            f"**Données de notation :**\n"
            f"- Note moyenne sur la période: {ratings_averages.get('daily_avg', 'N/A')}\n"
            f"- Note moyenne totale: {ratings_averages.get('total_avg', 'N/A')}\n\n"
            f"Structure de la réponse attendue :\n"
            f"1. **Bilan général des notations** (1-2 phrases)\n"
            f"2. **Points forts** (2-3 points max)\n"
            f"3. **Points faibles** (2-3 points max)\n"
            f"4. **Recommandations** (2-3 actions concrètes et priorisées)"
        )

        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not openai_api_key:
            return JsonResponse({'success': False, 'error': 'OPENAI_API_KEY non configurée sur le serveur.'}, status=500)

        headers = {
            'Authorization': f'Bearer {openai_api_key}',
            'Content-Type': 'application/json',
        }
        payload = {
            'model': 'gpt-3.5-turbo',
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.7,
            'max_tokens': 400,
        }
        
        try:
            openai_response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=payload, timeout=60)
            openai_response.raise_for_status()
            analysis_result = openai_response.json()['choices'][0]['message']['content']
            
            return JsonResponse({'success': True, 'data': {'analysis': analysis_result.strip()}})
        
        except requests.exceptions.RequestException as e:
            return JsonResponse({'success': False, 'error': f"Erreur de communication avec l'API OpenAI: {e}"}, status=502)

    except requests.exceptions.RequestException as e:
        return JsonResponse({'success': False, 'error': f"Erreur lors de la récupération des données internes: {e}"}, status=500)
    except Exception as e:
        logger.error(f"[ai_analysis_ratings] Erreur inattendue: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': 'Une erreur inattendue est survenue.'}, status=500)

@api_view(['GET'])
@authentication_classes([JWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def subscriptions_insights(request):
    """
    GET /api/insights/subscriptions?package_name=...&start=YYYY-MM-DD&end=YYYY-MM-DD
    Optionnel: country, product_id, base_plan_id, offer_id
    """
    err = _require_params(request, ['package_name', 'start', 'end'])
    if err: return err

    start = _parse_date(request.query_params.get('start'))
    end = _parse_date(request.query_params.get('end'))
    if not start or not end:
        return Response({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

    package_name = request.query_params.get('package_name')
    country = request.query_params.get('country')
    product_id = request.query_params.get('product_id')
    base_plan_id = request.query_params.get('base_plan_id')
    offer_id = request.query_params.get('offer_id')

    try:
        client = Client.objects.select_related('tenant').get(user=request.user)
        if not client.tenant:
            return Response({'success': False, 'error': 'No tenant configured.'}, status=400)
        tenant = client.tenant
    except Client.DoesNotExist:
        return Response({'success': False, 'error': 'Client not found.'}, status=404)

    qs = google_play_subscriptions_overview.objects.filter(
        tenant=tenant,
        package_name=package_name,
        date__gte=start,
        date__lte=end,
    )
    if country: qs = qs.filter(country=country)
    if product_id: qs = qs.filter(product_id=product_id)
    if base_plan_id: qs = qs.filter(base_plan_id=base_plan_id)
    if offer_id: qs = qs.filter(offer_id=offer_id)

    agg = qs.aggregate(
        new_subscribers=Sum('new_subscribers'),
        cancelled_subscribers=Sum('cancelled_subscribers'),
        active_subscribers=Sum('active_subscribers'),
    )

    churn = None
    if (agg.get('new_subscribers') or 0) > 0:
        churn = (agg.get('cancelled_subscribers') or 0) / max(1, (agg.get('new_subscribers') or 0))

    top_products = list(
        qs.values('product_id')
          .annotate(new_subscribers=Sum('new_subscribers'))
          .order_by('-new_subscribers')[:5]
    )

    data = {
        'package_name': package_name,
        'start': str(start),
        'end': str(end),
        'totals': agg,
        'approx_churn_ratio_cancel_over_new': churn,
        'top_products_by_new_subscribers': top_products,
    }
    return Response({'success': True, 'data': data})


@api_view(['GET'])
@authentication_classes([JWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def revenue_insights(request):
    """
    GET /api/insights/revenue?start=YYYY-MM-DD&end=YYYY-MM-DD
    Optionnel: package_name (si présent dans product_id), buyer_country, currency
    """
    err = _require_params(request, ['start', 'end'])
    if err: return err

    start = _parse_date(request.query_params.get('start'))
    end = _parse_date(request.query_params.get('end'))
    if not start or not end:
        return Response({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

    package_name = request.query_params.get('package_name')
    buyer_country = request.query_params.get('buyer_country')
    currency = request.query_params.get('currency')  # merchant currency

    try:
        client = Client.objects.select_related('tenant').get(user=request.user)
        if not client.tenant:
            return Response({'success': False, 'error': 'No tenant configured.'}, status=400)
        tenant = client.tenant
    except Client.DoesNotExist:
        return Response({'success': False, 'error': 'Client not found.'}, status=404)

    qs = google_play_earnings.objects.filter(
        tenant=tenant,
        transaction_date__gte=start,
        transaction_date__lte=end,
    )

    if package_name:
        qs = qs.filter(product_id__icontains=package_name)
    if buyer_country:
        qs = qs.filter(buyer_country=buyer_country)
    if currency:
        qs = qs.filter(merchant_currency=currency)

    agg = qs.aggregate(
        gross_merchant=Sum('amount_merchant_currency'),
        gross_buyer=Sum('amount_buyer_currency'),
        avg_conversion_rate=Avg('currency_conversion_rate'),
        tax_amount=Sum('tax_amount'),
        service_fee_amount=Sum('service_fee_amount'),
    )

    top_countries = list(
        qs.values('buyer_country')
          .annotate(amount=Sum('amount_merchant_currency'))
          .order_by('-amount')[:5]
    )

    data = {
        'start': str(start),
        'end': str(end),
        'totals': agg,
        'top_countries_by_revenue': top_countries,
    }
    return Response({'success': True, 'data': data})


@api_view(['GET'])
@authentication_classes([JWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def crashes_insights(request):
    """
    GET /api/insights/crashes?package_name=...&start=YYYY-MM-DD&end=YYYY-MM-DD
    Optionnel: app_version, device, os_version, android_os_version
    """
    err = _require_params(request, ['start', 'end'])
    if err: return err

    start = _parse_date(request.query_params.get('start'))
    end = _parse_date(request.query_params.get('end'))
    if not start or not end:
        return Response({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

    package_name = request.query_params.get('package_name')
    app_version = request.query_params.get('app_version')
    device = request.query_params.get('device')
    os_version = request.query_params.get('os_version')
    android_os_version = request.query_params.get('android_os_version')

    try:
        client = Client.objects.select_related('tenant').get(user=request.user)
        if not client.tenant:
            return Response({'success': False, 'error': 'No tenant configured.'}, status=400)
        tenant = client.tenant
    except Client.DoesNotExist:
        return Response({'success': False, 'error': 'Client not found.'}, status=404)

    if not package_name:
        package_name = _get_default_package_for_tenant(tenant)
        if not package_name:
            return Response({'success': False, 'error': 'No packages found for tenant.'}, status=404)

    qs = google_play_crashes_overview.objects.filter(
        tenant=tenant,
        package_name=package_name,
        date__gte=start,
        date__lte=end,
    )
    if app_version: qs = qs.filter(app_version=app_version)
    if device: qs = qs.filter(device=device)
    if os_version: qs = qs.filter(os_version=os_version)
    if android_os_version: qs = qs.filter(android_os_version=android_os_version)

    agg = qs.aggregate(
        daily_crashes=Sum('daily_crashes'),
        daily_anrs=Sum('daily_anrs'),
    )

    top_versions = list(
        qs.values('app_version')
          .annotate(crashes=Sum('daily_crashes'))
          .order_by('-crashes')[:5]
    )

    top_devices = list(
        qs.values('device')
          .annotate(crashes=Sum('daily_crashes'))
          .order_by('-crashes')[:5]
    )
    top_android_os_versions = list(
        qs.values('android_os_version')
          .annotate(crashes=Sum('daily_crashes'))
          .order_by('-crashes')[:5]
    )

    data = {
        'package_name': package_name,
        'start': str(start),
        'end': str(end),
        'totals': agg,
        'top_versions_by_crashes': top_versions,
        'top_devices_by_crashes': top_devices,
        'top_android_os_versions_by_crashes': top_android_os_versions,
    }
    return Response({'success': True, 'data': data})


@api_view(['GET'])
@authentication_classes([JWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def ratings_insights(request):
    """
    GET /api/insights/ratings?package_name=...&start=YYYY-MM-DD&end=YYYY-MM-DD
    Optionnel: device
    """
    err = _require_params(request, ['start', 'end'])
    if err: return err

    start = _parse_date(request.query_params.get('start'))
    end = _parse_date(request.query_params.get('end'))
    if not start or not end:
        return Response({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

    package_name = request.query_params.get('package_name')
    device = request.query_params.get('device')

    try:
        client = Client.objects.select_related('tenant').get(user=request.user)
        if not client.tenant:
            return Response({'success': False, 'error': 'No tenant configured.'}, status=400)
        tenant = client.tenant
    except Client.DoesNotExist:
        return Response({'success': False, 'error': 'Client not found.'}, status=404)

    if not package_name:
        package_name = _get_default_package_for_tenant(tenant)
        if not package_name:
            return Response({'success': False, 'error': 'No packages found for tenant.'}, status=404)

    qs = google_play_ratings_overview.objects.filter(
        tenant=tenant,
        package_name=package_name,
        date__gte=start,
        date__lte=end,
    )
    if device: qs = qs.filter(device=device)

    agg = qs.aggregate(
        daily_avg=Avg('daily_average_rating'),
        total_avg=Avg('total_average_rating'),
    )

    # Averages by device for highlight
    top_devices_avg = list(
        qs.values('device')
          .annotate(avg_rating=Avg('daily_average_rating'))
          .order_by('-avg_rating')[:5]
    )

    data = {
        'package_name': package_name,
        'start': str(start),
        'end': str(end),
        'averages': agg,
        'top_devices_by_avg_rating': top_devices_avg,
    }
    return Response({'success': True, 'data': data})
