from django.apps import AppConfig

class MywebsiteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mywebsite'

    def ready(self):
        import mywebsite.signals