from django.apps import apps

# Dictionnaire central pour mapper les noms de rapports aux modèles Django
REPORT_MODEL_MAPPING = {
    'installs': 'google_play_installs_overview',
    'revenue': 'google_play_earnings',
    'subscriptions': 'google_play_subscriptions_overview',
    'reviews': 'google_play_reviews',
    'sales': 'google_play_sales',
    'crashes': 'google_play_crashes_overview',
    'ratings': 'google_play_ratings_overview',
}

def list_available_reports():
    """Retourne la liste des clés des rapports disponibles."""
    return list(REPORT_MODEL_MAPPING.keys())

def get_model_for_report(report_type):
    """Récupère la classe du modèle Django pour un type de rapport donné."""
    model_name = REPORT_MODEL_MAPPING.get(report_type)
    if not model_name:
        return None
    try:
        return apps.get_model('play_reports', model_name)
    except LookupError:
        return None

def get_report_queryset(report_type):
    """Retourne le queryset pour un type de rapport donné."""
    model_class = get_model_for_report(report_type)
    if model_class:
        return model_class.objects.all()
    return None
