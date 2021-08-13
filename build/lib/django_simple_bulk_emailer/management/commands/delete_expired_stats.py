from django.conf import (
    settings,
)
from django.core.management.base import (
    BaseCommand,
)
from django.utils import (
    timezone,
)


from ...models import (
    MonthlyStat,
)


class Command(BaseCommand):
    help = 'Deletes monthly stats that have reached or passed their deletion date'

    def handle(self, *args, **options):
        try:
            months_saved = settings.EMAILER_STATS_SAVED
        except AttributeError:
            months_saved = 12
        now = timezone.now().date()
        current_year = now.year
        current_month = now.month
        monthly_stats = MonthlyStat.objects.all()
        for stats in monthly_stats:
            months_old = ((current_year - stats.year_int) * 12) + current_month - stats.month_int
            if months_old >= months_saved:
                stats.delete()
