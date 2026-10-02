"""
Django settings for O.P.S. (Over-Engineered Programmed System) project.
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'ops-local-dev-secret-key-change-in-production'

DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    'channels',
    'rest_framework',
    'corsheaders',

    # O.P.S Core App
    'ops_core',
]

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ops_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ops_backend.wsgi.application'
ASGI_APPLICATION = 'ops_backend.asgi.application'

# Primary Relational Database: PostgreSQL 18
# Configured for persistent user workstation memories, safety logs, and permissions
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'ops_db'),
        'USER': os.getenv('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
        'HOST': os.getenv('POSTGRES_HOST', '127.0.0.1'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }
}

try:
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.0)
    s.connect((DATABASES['default']['HOST'], int(DATABASES['default']['PORT'])))
    s.close()
except Exception:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'ops_db.sqlite3',
    }

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOW_ALL_ORIGINS = True

# O.P.S ChromaDB Vector Storage Configuration
CHROMA_STORAGE_DIR = BASE_DIR / 'chroma_storage'

# O.P.S Ollama Tri-Model Configuration (Per OPS_Local_LLM_Model_Roles.md)
# Model 1: Fast Router and Intent Detection (Qwen3 0.6B)
OLLAMA_ROUTER_MODEL = os.getenv("OLLAMA_ROUTER_MODEL", "hf.co/Qwen/Qwen3-0.6B-GGUF:Q8_0")

# Model 2: Main Reasoning, Planning, Code Gen, and Debugging (Qwen3 1.7B)
OLLAMA_REASONING_MODEL = os.getenv("OLLAMA_REASONING_MODEL", "hf.co/Qwen/Qwen3-1.7B-GGUF:Q8_0")

# Model 3: Conversation, Content Generation, and Jarvis Personality Layer (Llama 3.2 1B Instruct)
OLLAMA_CONVERSATION_MODEL = os.getenv("OLLAMA_CONVERSATION_MODEL", "hf.co/hugging-quants/Llama-3.2-1B-Instruct-Q8_0-GGUF:Q8_0")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

