from django.apps import AppConfig
from .firebase_init import initialize_firebase

class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        initialize_firebase()
