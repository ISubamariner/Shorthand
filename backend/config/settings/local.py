from .base import *  # noqa: F401,F403

DEBUG = True

SECRET_KEY = "insecure-dev-key-for-local-only"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "shorthand",
        "USER": "shorthand",
        "PASSWORD": "shorthand",
        "HOST": "db",
        "PORT": "5432",
    }
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

ALLOWED_HOSTS = ["*"]
