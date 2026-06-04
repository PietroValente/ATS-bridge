import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "dev-only-not-a-secret"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = ["db_models"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("DB_PATH", str(BASE_DIR / "pdm.db")),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
ROOT_URLCONF = "push_data_manager.urls"
WSGI_APPLICATION = "push_data_manager.wsgi.application"
