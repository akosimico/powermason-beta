import ssl

ssl._create_default_https_context = ssl._create_unverified_context

import os
import sys
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'powermason_capstone.settings')

application = get_wsgi_application()
