import os

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ["DISABLE_JOB_WORKERS"] = "1"
os.environ["DISABLE_MONITORING_WORKER"] = "1"

from .base import *  # noqa: F401,F403

DEBUG = True

SECRET_KEY = "test-secret-key-not-for-production"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]
ALLOWED_HOSTS = ["*"]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
