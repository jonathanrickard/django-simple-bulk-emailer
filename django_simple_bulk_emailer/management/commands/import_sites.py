from django.contrib.sites.models import (
    Site,
)
from django.core.management.base import (
    BaseCommand,
)


from ...models import (
    SiteProfile,
)


class Command(BaseCommand):
    help = 'Creates a SiteProfile instance for each instance in the Django sites framework'

    def handle(self, *args, **options):
        sites = Site.objects.all()
        for site in sites:
            site_profile, created = SiteProfile.objects.get_or_create(
                site_ptr=site,
            )
            site_profile.domain = site.domain
            site_profile.name = site.name
            site_profile.save()
