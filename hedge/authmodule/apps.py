from django.apps import AppConfig


class AuthmoduleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authmodule'

    def ready(self):
        # Import signals here to ensure they are registered
        import authmodule.signals

