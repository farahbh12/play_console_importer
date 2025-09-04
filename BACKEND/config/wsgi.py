"""
WSGI config for play_console_importer project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project directory to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    logger.info("WSGI application loaded successfully")
except Exception as e:
    logger.error(f"Error loading WSGI application: {str(e)}")
    raise
