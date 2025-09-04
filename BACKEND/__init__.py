"""
WSGI config for play_console_importer project.

This module contains the WSGI application used by Django's development server.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
