from django.apps import AppConfig
# from django.db.models.signals import pre_save

class AplicativoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'aplicativo'

    # def ready(self):
        # import aplicativo.signals  

