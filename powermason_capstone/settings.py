from pathlib import Path
import os
from django.contrib.messages import constants as messages
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")
ENVIRONMENT = os.getenv("ENVIRONMENT")
POSTGRES_LOCALLY = os.getenv("POSTGRES_LOCALLY")


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-mgi*0-a4^pv-6109$koden*5s+c=l3@qi-2&v%rn8=u4wvmkdk"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Application definition
TIME_ZONE = "Asia/Manila"
USE_TZ = True

INSTALLED_APPS = [
    "authentication",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.sites",
    "widget_tweaks",
    "project_profiling",
    "scheduling",
    "progress_monitoring",
    "notifications",
    "manage_client",
    "materials_equipment",
    "xero",
    "employees",
]
SITE_ID = 1

MESSAGE_TAGS = {
    messages.DEBUG: "bg-gray-200 text-gray-800",
    messages.INFO: "bg-blue-100 text-blue-800",
    messages.SUCCESS: "bg-green-100 text-green-800",
    messages.WARNING: "bg-yellow-100 text-yellow-800",
    messages.ERROR: "bg-red-100 text-red-800",
}

MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "authentication.middleware.LimitMessagesMiddleware",
]

CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
]
ROOT_URLCONF = "powermason_capstone.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "authentication.utils.context_processors.user_context",
                "notifications.context_processors.unread_notifications",
                "django.template.context_processors.media",
                "powermason_capstone.core.context_processors.app_version",
            ],
        },
    },
]

WSGI_APPLICATION = "powermason_capstone.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
# URL to access static files
STATIC_URL = "/static/"

# Local static files (for development)
STATICFILES_DIRS = [os.path.join(BASE_DIR, "powermason_capstone/static")]

# Where collectstatic will put all files for production
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": os.getenv("OAUTH_GOOGLE_CLIENT_ID"),
            "secret": os.getenv("OAUTH_GOOGLE_SECRET_KEY"),
        },
    },
    "xero": {
        "APP": {
            "client_id": os.getenv("XERO_CLIENT_ID"),
            "secret": os.getenv("XERO_CLIENT_SECRET"),
        },
        "SCOPE": [
            "accounting.transactions",
            "accounting.contacts",
            "accounting.settings",
        ],
    },
}
XERO_CLIENT_ID = os.getenv("XERO_CLIENT_ID")
XERO_CLIENT_SECRET = os.getenv("XERO_CLIENT_SECRET")
XERO_REDIRECT_URI = "http://localhost:8000/accounts/xero/login/callback/"

# Email Configuration
# Use SendGrid for production (Render-compatible)
if ENVIRONMENT == "production" or POSTGRES_LOCALLY == True:
    if os.getenv("SENDGRID_API_KEY"):
        # Use SendGrid HTTP API (works on Render - bypasses SMTP port blocking)
        EMAIL_BACKEND = "authentication.backends.sendgrid_backend.SendGridHTTPBackend"
        SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")  # Used by custom backend
        ACCOUNT_EMAIL_SUBJECT_PREFIX = ""
        DEFAULT_FROM_EMAIL = "Powermason <powermasonwebsite@gmail.com>"
        SERVER_EMAIL = "powermasonwebsite@gmail.com"
        print("Email configured for production with SendGrid HTTP API")
    elif os.getenv("EMAIL_ADDRESS") and os.getenv("EMAIL_HOST_PASSWORD"):
        # Fallback to Gmail SMTP (may not work on Render)
        EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
        EMAIL_HOST = "smtp.gmail.com"
        EMAIL_HOST_USER = os.getenv("EMAIL_ADDRESS")
        EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
        EMAIL_PORT = 587
        EMAIL_USE_TLS = True
        EMAIL_USE_SSL = False
        EMAIL_TIMEOUT = 5  # Reduced from 30 to prevent Render request timeouts
        EMAIL_CONNECTION_TIMEOUT = 3  # Reduced from 10 for faster failures
        ACCOUNT_EMAIL_SUBJECT_PREFIX = ""
        DEFAULT_FROM_EMAIL = "Powermason <powermasonwebsite@gmail.com>"
        SERVER_EMAIL = "powermasonwebsite@gmail.com"
        print("Email configured for production with Gmail SMTP (may not work on Render)")
    else:
        EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
        print("Email configured for production (console backend - no credentials)")
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    print("Email configured for development (console backend)")

# Messages Configuration - ADD THIS
MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

# Allauth Configuration
SOCIALACCOUNT_LOGIN_ON_GET = True
AUTH_USER_MODEL = "authentication.CustomUser"
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = "none" #RENDER DEPLOYMENT CHANGED TO MANDATORY WHEN MAY PERA NA
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 5
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 300

# Redirect URLs - ADD THESE
LOGIN_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/accounts/login/"
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = "/"  # ← ADD THIS
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = "/accounts/login/"  # ← ADD THIS

ACCOUNT_FORMS = {
    "signup": "authentication.forms.CustomSignupForm",
}

# Site settings
ACCOUNT_EMAIL_SUBJECT_PREFIX = "[Powermason] "

# Custom adapter
ACCOUNT_ADAPTER = "authentication.utils.adapters.CustomAccountAdapter"
ACCOUNT_EMAIL_CONFIRMATION_HMAC = False
