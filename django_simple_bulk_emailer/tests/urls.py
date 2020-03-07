from django.urls import (
    include,
    path,
)
from django.contrib import (
    admin,
)


urlpatterns = [
      path(
          'admin/',
          admin.site.urls,
      ),
      path(
          'mail_test/',
          include('django_simple_bulk_emailer.urls'),
      ),
]
