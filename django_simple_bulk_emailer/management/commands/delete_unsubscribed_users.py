from datetime import (
    timedelta,
)


from django.core.management.base import (
    BaseCommand,
)
from django.utils import (
    timezone,
)


from ...models import (
    Subscriber,
)


class Command(BaseCommand):
    help = 'Deletes subscribers who do not have any subscriptions'

    def handle(self, *args, **options):
        one_day_ago = timezone.now() - timedelta(days=1)
        Subscriber.objects.filter(
            subscriptions=None,
        ).filter(
            created__lte=one_day_ago,
        ).delete()
