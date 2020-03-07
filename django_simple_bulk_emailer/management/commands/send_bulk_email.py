from django.contrib.sites.models import (
    Site,
)
from django.core.management.base import (
    BaseCommand,
)
from django.urls import (
    reverse,
)
from django.utils import (
    timezone,
)
from django.utils.formats import (
    localize,
)


from ...views import (
    get_universal_email_directory,
    send_email,
)
from ...models import (
    EmailTracker,
    SiteProfile,
    Subscriber,
    Subscription,
)


class Command(BaseCommand):
    help = 'Sends bulk email'

    def handle(self, *args, **options):
        subscriptions = Subscription.objects.order_by(
            'sort_order',
        )
        if subscriptions:
            for subscription in subscriptions:
                email_instance = subscription.get_email_class().objects.filter(
                    sendable=True,
                ).filter(
                    subscription_list=subscription,
                ).order_by(
                    'updated',
                ).first()
                if email_instance:
                    break
            if email_instance:
                ''' Make unavailable to other instances of the function '''
                email_instance.sendable = False
                email_instance.save()
                ''' Create tracker '''
                tracker = EmailTracker.objects.create(
                    subject=email_instance.email_subject(),
                    subscription_name=email_instance.subscription_list.list_name,
                )
                ''' Create email '''
                email_directory = subscription.email_directory
                basic_template = '{}/bulk_email_send.html'.format(get_universal_email_directory())
                text_template = '{}/email_template_text.txt'.format(email_directory)
                html_template = '{}/email_template_html.html'.format(email_directory)
                site_domain = Site.objects.get_current().domain
                site_profile = SiteProfile.objects.filter(
                    domain=site_domain,
                ).first()
                protocol_domain = site_profile.protocol_domain()
                email_content = {
                    'basic_template': basic_template,
                    'protocol_domain': protocol_domain,
                    'email_instance': email_instance,
                }
                ''' Get subscribers '''
                subscriber_list = Subscriber.objects.filter(
                    subscriptions=subscription,
                )
                ''' Set number_sent at 0 '''
                number_sent = 0
                for subscriber in subscriber_list:
                    ''' Get subscriber-specific information '''
                    tracking_image = reverse(
                        'django_simple_bulk_emailer:opened_email',
                        kwargs={
                            'pk': tracker.pk,
                            'subscriber_key': subscriber.subscriber_key,
                        },
                    )
                    email_content['tracking_image'] = tracking_image
                    to_address = '"{} {}" <{}>'.format(
                        subscriber.first_name,
                        subscriber.last_name,
                        subscriber.subscriber_email,
                    )
                    ''' Send email '''
                    send_email(
                        email_content,
                        list_slug=subscription.list_slug,
                        subscriber_key=subscriber.subscriber_key,
                        text_template=text_template,
                        html_template=html_template,
                        subject=email_instance.email_subject(),
                        to_address=to_address,
                    )
                    ''' Increase number_sent by 1 '''
                    number_sent += 1
                ''' Create send history '''
                send_complete = timezone.now()
                email_instance.send_history = '<ul><li>Completed: {}<ul><li>Sent to: {}</li></ul></li></ul>{}'.format(
                    localize(timezone.localtime(send_complete)),
                    email_instance.subscription_list,
                    email_instance.send_history,
                )
                ''' Release email to be sent again '''
                email_instance.sending = False
                email_instance.save()
                ''' Update tracker '''
                tracker.send_complete = send_complete
                tracker.number_sent = number_sent
                tracker.save()
