from django.urls import (
    path,
)


from .views import (
    email_preview,
    get_subscriptions,
    list_view,
    manage_subscriptions,
    mc_sync,
    opened_email,
    page_preview,
    page_view,
    quick_unsubscribe,
)


app_name = 'django_simple_bulk_emailer'


urlpatterns = [
    path(
        '<list_slug>/',
        list_view,
        name='list_view',
    ),
    path(
        'email-preview/<list_slug>/<pk>/',
        email_preview,
        name='email_preview',
    ),
    path(
        '<list_slug>/<year>/<month>/<day>/<pk>/<headline_slug>.html',
        page_view,
        name='page_view',
    ),
    path(
        'page-preview/<list_slug>/<year>/<month>/<day>/<pk>/<headline_slug>.html',
        page_preview,
        name='page_preview',
    ),
    path(
        'subscriptions/subscribe/',
        get_subscriptions,
        name='get_subscriptions',
    ),
    path(
        'subscriptions/manage/<subscriber_key>/',
        manage_subscriptions,
        name='manage_subscriptions',
    ),
    path(
        'subscriptions/quick-unsubscribe/<list_slug>/<subscriber_key>/',
        quick_unsubscribe,
        name='quick_unsubscribe',
    ),
    path(
        'load-image/<pk>/<subscriber_key>.png',
        opened_email,
        name='opened_email',
    ),
    path(
        'mc-sync/sync/',
        mc_sync,
        name='mc_sync',
    ),
]
