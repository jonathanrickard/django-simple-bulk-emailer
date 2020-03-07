import hashlib
from random import (
    choice,
)
from string import (
    ascii_lowercase,
    ascii_uppercase,
    digits,
)


from django.core.exceptions import (
    ObjectDoesNotExist,
)
from django.db.models.signals import (
    m2m_changed,
    pre_delete,
    pre_save,
)


from ..models import (
    Subscriber,
    Subscription,
)


def class_set(input_set):
    unchecked_classes = input_set
    unchecked_subclasses = set()
    output_classes = set()
    while len(unchecked_classes) > 0:
        for unchecked_item in unchecked_classes:
            unchecked_subclasses.update(unchecked_item.__subclasses__())
            output_classes.add(unchecked_item)
        unchecked_classes = unchecked_subclasses
        unchecked_subclasses = set()
    return output_classes


def save_sync(sender, instance, *args, **kwargs):
    instance.subscriber_key = ''.join(choice(ascii_lowercase + ascii_uppercase + digits) for _ in range(64))
    instance.subscriber_email = instance.subscriber_email.lower()
    if not instance.mc_email:
        instance.mc_email = instance.subscriber_email
    try:
        saved_object = instance.__class__.objects.get(
            pk=instance.pk,
        )
        changeable_fields = [
            'first_name',
            'last_name',
            'subscriber_email',
        ]
        for field in changeable_fields:
            if getattr(instance, field) != getattr(saved_object, field):
                instance.mc_synced = False
                break
    except ObjectDoesNotExist:
        pass


def m2m_sync(sender, instance, *args, **kwargs):
    instance.mc_synced = False
    instance.save()


def delete_sync(sender, instance, *args, **kwargs):
    subscriber_hash = hashlib.md5(instance.mc_email.encode('utf-8')).hexdigest()
    subscriptions = Subscription.objects.filter(
        mc_sync=True,
    )
    for subscription in subscriptions:
        if subscription in instance.subscriptions.all():
            client = MailChimp(
                mc_api=subscription.mc_api,
                mc_user=subscription.mc_user,
            )
            try:
                client.lists.members.update(
                    list_id=subscription.mc_list,
                    subscriber_hash=subscriber_hash,
                    data={
                        'status': 'unsubscribed',
                    },
                )
            except MailChimpError:
                pass


try:
    from mailchimp3 import MailChimp
    from mailchimp3.mailchimpclient import MailChimpError
    for class_item in class_set(set({Subscriber})):
        pre_save.connect(save_sync, class_item)
        m2m_changed.connect(m2m_sync, class_item.subscriptions.through)
        pre_delete.connect(delete_sync, class_item)
except ImportError:
    pass
