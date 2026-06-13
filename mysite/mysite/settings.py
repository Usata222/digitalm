import cloudinary
import cloudinary_storage
from pathlib import Path

# ============================================================
# [NEW] — python-dotenv import
# We import os and load_dotenv so Django can read values
# from the .env file. os.environ.get() is how we pull them.
# ============================================================
import os
from dotenv import load_dotenv

load_dotenv()  # [NEW] — Loads the .env file into the environment
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# [CHANGED] — SECRET_KEY
# Was:    SECRET_KEY = 'django-insecure-oehz24m567u...'
# Now:    Read from .env so the real key never hits GitHub.
# ============================================================
SECRET_KEY = os.environ.get('SECRET_KEY')
# ============================================================

# ============================================================
# [CHANGED] — DEBUG
# Was:    DEBUG = True  (hardcoded)
# Now:    Read from .env. Value in .env should be True or False.
#         The == 'True' converts the string from .env to a bool.
# ============================================================
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
# ============================================================

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'cloudinary',
    'cloudinary_storage',
    'myapp',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mysite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mysite.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}



# ============================================================
# [CHANGED] — STRIPE KEYS
# Was:    STRIPE_SECRET_KEY = "sk_test_51TTR..."  (hardcoded)
#         STRIPE_PUBLISHABLE_KEY = "pk_test_51TTR..."  (hardcoded)
# Now:    Both read from .env. If these end up on GitHub,
#         Stripe could flag or revoke the keys automatically.
# ============================================================
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
# ============================================================


# ============================================================
# [CHANGED] — CLOUDINARY_STORAGE
# Was: dict only — django-cloudinary-storage reads this dict
#      for the storage backend, but the raw `cloudinary` SDK
#      (imported at the top of this file) was never configured
#      via cloudinary.config(), so direct SDK calls would be
#      unauthenticated.
# Now: same dict PLUS an explicit cloudinary.config() call.
# ============================================================
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.environ.get("CLOUDINARY_CLOUD_NAME"),
    "API_KEY": os.environ.get("CLOUDINARY_API_KEY"),
    "API_SECRET": os.environ.get("CLOUDINARY_API_SECRET"),
}

cloudinary.config(  # [NEW]
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True,
)
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

# ============================================================
# [CHANGED] — MEDIA_URL / MEDIA_ROOT
# Was: both commented out, but urls.py calls
#      static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
#      which raises AttributeError if these don't exist at all.
# Now: defined so urls.py doesn't crash. They're effectively
#      unused for actual file serving since DEFAULT_FILE_STORAGE
#      points to Cloudinary (all uploads go there), but Django
#      still references these attributes internally in places.
# ============================================================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
# ============================================================


LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = 'login'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"