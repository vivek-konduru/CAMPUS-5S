"""
WSGI config for fiveSManagement project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
import django

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fiveSManagement.settings')

django.setup()
from django.core.management import call_command
try:
    call_command('makemigrations')
    call_command('migrate')
except Exception as e:
    print(f"Migration error: {e}")


application = get_wsgi_application()
