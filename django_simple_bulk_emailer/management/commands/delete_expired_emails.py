from django.core.management.base import (
    BaseCommand,
)
from django.utils import (
    timezone,
)


from ...models import (
    BulkEmail,
)


class Command(BaseCommand):
    help = 'Deletes emails that have reached or passed their deletion date'

    def handle(self, *args, **options):
        BulkEmail.objects.filter(
            deletion_date__lte=timezone.now().date(),
        ).delete()
