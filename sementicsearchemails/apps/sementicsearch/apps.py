import os
from dotenv import load_dotenv
from django.apps import AppConfig


class SementicsearchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.sementicsearch'

    def ready(self):
        from .services.vectorizer import laod_model
        laod_model()