import hashlib


from django.core.management.base import (
    BaseCommand,
)


from mailchimp3 import (
    MailChimp,
)
from mailchimp3.mailchimpclient import (
    MailChimpError,
)


from ...models import (
    Subscriber,
    Subscription,
)


def get_client(subscription):
    client = MailChimp(
        mc_api=subscription.mc_api,
        mc_user=subscription.mc_user,
        timeout=30.0,
    )
    return client


def get_hash(email_address):
    return hashlib.md5(email_address.encode('utf-8')).hexdigest()


class Command(BaseCommand):
    help = 'Syncs subscriber data to MailChimp'

    def handle(self, *args, **options):
        """ """
        ''' Get subscribers that are not yet synced '''
        subscribers = Subscriber.objects.filter(
            mc_synced=False,
        )
        ''' Get subscriptions that are set up for syncing '''
        all_subscriptions = Subscription.objects.filter(
            mc_sync=True,
        )
        ''' For each subscriber, try to create or update a subscribed MailChimp contact '''
        for subscriber in subscribers:
            ''' Try to pass subscriber data to MailChimp client using mc_email address hash '''
            subscriber_hash = get_hash(subscriber.mc_email)
            for subscription in all_subscriptions:
                client = get_client(subscription)
                subscriber_data = {
                    'status_if_new': 'subscribed',
                    'status': 'subscribed',
                    'email_address': subscriber.subscriber_email,
                    'merge_fields': {
                        'FNAME': subscriber.first_name,
                        'LNAME': subscriber.last_name,
                    },
                }
                try:
                    client.lists.members.create_or_update(
                        list_id=subscription.mc_list,
                        subscriber_hash=subscriber_hash,
                        data=subscriber_data,
                    )
                    print('Created or updated contact {} as {} in list {}'.format(
                        subscriber.mc_email,
                        subscriber.subscriber_email,
                        subscription.list_name,
                    ))
                except MailChimpError:
                    print('Unable to create or update contact {} as {} in list {}'.format(
                        subscriber.mc_email,
                        subscriber.subscriber_email,
                        subscription.list_name,
                    ))
                    try:
                        ''' If unable to pass subscriber data to MailChimp client, try subscriber_email address hash '''
                        subscriber_hash = get_hash(subscriber.subscriber_email)
                        client.lists.members.create_or_update(
                            list_id=subscription.mc_list,
                            subscriber_hash=subscriber_hash,
                            data=subscriber_data,
                        )
                        print('Created or updated contact {} in list {}'.format(
                            subscriber.subscriber_email,
                            subscription.list_name,
                        ))
                    except MailChimpError:
                        print('Unable to create or update contact {} in list {}'.format(
                            subscriber.subscriber_email,
                            subscription.list_name,
                        ))
                        ''' Remove subscription from subscriber if cannot be synced to MailChimp '''
                        subscriber.subscriptions.remove(subscription)
                        print('Removed subscription {} from subscriber {}'.format(
                            subscription.list_name,
                            subscriber.subscriber_email,
                        ))

            ''' For each nonsubscribed subscriber, try to unsubscribe its corresponding MailChimp contact '''
            subscriber_hash = get_hash(subscriber.subscriber_email)
            subscriber_subscriptions = subscriber.subscriptions.filter(
                mc_sync=True,
            )
            for subscription in all_subscriptions:
                if subscription not in subscriber_subscriptions:
                    client = get_client(subscription)
                    subscriber_data = {
                        'status': 'unsubscribed',
                    }
                    try:
                        client.lists.members.update(
                            list_id=subscription.mc_list,
                            subscriber_hash=subscriber_hash,
                            data=subscriber_data,
                        )
                        print('Unsubscribed contact {} from list {}'.format(
                            subscriber.subscriber_email,
                            subscription.list_name,
                        ))
                    except MailChimpError:
                        print('Unable to unsubscribe contact {} from list {}'.format(
                            subscriber.subscriber_email,
                            subscription.list_name,
                        ))
            ''' Update the subscriber object's attributes '''
            subscriber.mc_email = subscriber.subscriber_email
            subscriber.mc_synced = True
            subscriber.save()
            print('Completed syncing MailChimp for contact {} in list {}'.format(
                subscriber.subscriber_email,
                subscription.list_name,
            ))
