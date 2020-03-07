from django.apps import (
    AppConfig,
)


class Config(AppConfig):
    name = 'django_simple_bulk_emailer'
    verbose_name = 'Bulk email'

    def ready(self):
        from .signals import (
            handlers,
        )
