from datetime import (
    timedelta,
)
from unittest.mock import (
    patch,
)


from django.contrib.sites.models import (
    Site,
)
from django.test import (
    TestCase,
)
from django.utils import (
    timezone,
)
from django.utils.formats import (
    localize,
)


from django_simple_bulk_emailer.models import (
    BulkEmail,
    EmailDocument,
    EmailImage,
    Subscription,
)


from .functions import (
    attribute_equals,
    attribute_length_equals,
    clear_data_and_files,
    create_email,
    create_site_profile,
    create_stats,
    create_subscription,
    create_subscriber,
    create_tracker,
    fake_now,
    method_output_contains,
    method_output_equals,
    method_output_length_equals,
)


class MixinWrap:
    class BaseMixin(TestCase):
        longMessage = False

        def tearDown(self):
            clear_data_and_files()
            super().tearDown()


class SiteProfileTests(MixinWrap.BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.test_instance = create_site_profile()
        super().setUp()

    def test_protocol_domain(self):
        method_output_equals(
            self,
            'protocol_domain',
            'http://127.0.0.1:8000',
        )


class SubscriptionTests(MixinWrap.BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.test_instance = create_subscription()
        test_subscriber = create_subscriber()
        test_subscriber.subscriptions.add(self.test_instance)
        super().setUp()

    def test_save(self):
        attribute_equals(
            self,
            {
                'list_slug': 'test-list',
            },
        )

    def test_get_email_class(self):
        method_output_equals(
            self,
            'get_email_class',
            BulkEmail,
        )

    def test_list_link(self):
        method_output_contains(
            self,
            'list_link',
            '<a href="',
        )
        method_output_contains(
            self,
            'list_link',
            '/test-list/" target="_blank">Page</a>',
        )

    def test_subscriber_count(self):
        method_output_equals(
            self,
            'subscriber_count',
            '1',
        )


class SubscriberTests(MixinWrap.BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.test_instance = create_subscriber(subscriber_email='Example@Example.com')
        test_subscription_one = create_subscription(list_name='Test Subscription One')
        self.test_instance.subscriptions.add(test_subscription_one)
        test_subscription_two = create_subscription(list_name='Test Subscription Two')
        self.test_instance.subscriptions.add(test_subscription_two)
        super().setUp()

    def test_save(self):
        attribute_length_equals(
            self,
            'subscriber_key',
            64,
        )
        attribute_equals(
            self,
            {
                'subscriber_email': 'example@example.com',
            },
        )

    def test_str(self):
        method_output_equals(
            self,
            '__str__',
            'example@example.com',
        )

    def test_subscription_lists(self):
        method_output_equals(
            self,
            'subscription_lists',
            'Test Subscription One, Test Subscription Two',
        )


class BulkEmailTests(MixinWrap.BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        with patch(
            'django_simple_bulk_emailer.models.timezone.now',
            fake_now,
        ):
            self.profile_instance = create_site_profile()
            with self.settings(
                EMAILER_EMAIL_DELETE_DAYS=30,
            ):
                self.test_instance = create_email()
        super().setUp()

    def test_get_deletion_date(self):
        future_time = fake_now() + timedelta(days=30)
        attribute_equals(
            self,
            {
                'deletion_date': future_time.date(),
            },
        )

    def test_short_headline(self):
        method_output_length_equals(
            self,
            'short_headline',
            30,
        )

    def test_short_headline_shorter(self):
        self.test_instance.headline = 'Shorter headline'
        self.test_instance.save()
        method_output_equals(
            self,
            'short_headline',
            'Shorter headline',
        )

    def test_str(self):
        method_output_equals(
            self,
            '__str__',
            'Test headline of many chara...',
        )

    def test_first_paragraph(self):
        method_output_equals(
            self,
            'first_paragraph',
            'Test body text paragraph one.',
        )

    def test_email_subject(self):
        method_output_equals(
            self,
            'email_subject',
            'Test headline of many characters',
        )

    def test_email_subject_updated(self):
        self.test_instance.is_updated = True
        self.test_instance.save()
        method_output_equals(
            self,
            'email_subject',
            'Updated: Test headline of many characters',
        )

    def test_email_headline(self):
        method_output_equals(
            self,
            'email_headline',
            'Test headline of many characters',
        )

    def test_email_body(self):
        method_output_equals(
            self,
            'email_body',
            '<p>Test body text paragraph one.</p><p>Test body text paragraph two.</p>',
        )

    def test_email_body_substitutions(self):
        with self.settings(
            EMAILER_SUBSTITUTIONS={
                'Test': 'Substitute',
                '</p><p>': '<br><br>',
            },
        ):
            method_output_equals(
                self,
                'email_body',
                '<p>Substitute body text paragraph one.<br><br>Substitute body text paragraph two.</p>',
            )

    def test_email_image(self):
        image_instance = EmailImage.objects.all().first()
        method_output_equals(
            self,
            'email_image',
            image_instance,
        )

    def test_email_documents(self):
        document_instance = EmailDocument.objects.all().first()
        method_output_contains(
            self,
            'email_documents',
            document_instance,
        )

    def test_subscription_name(self):
        subscription_list_name = Subscription.objects.all().first().list_name
        method_output_equals(
            self,
            'subscription_name',
            subscription_list_name,
        )

    def test_subscription_name_unassigned(self):
        self.test_instance.subscription_list = None
        self.test_instance.save()
        method_output_equals(
            self,
            'subscription_name',
            'None chosen',
        )

    def test_headline_slug(self):
        method_output_equals(
            self,
            'headline_slug',
            'test-headline-of-many-characters',
        )

    def test_subscription_url(self):
        method_output_contains(
            self,
            'subscription_url',
            '/test-list/',
        )

    def test_page_url(self):
        method_output_contains(
            self,
            'page_url',
            '/test-list/',
        )
        method_output_contains(
            self,
            'page_url',
            '/test-headline-of-many-characters.html',
        )

    def test_page_preview(self):
        method_output_contains(
            self,
            'page_preview',
            '<a href="',
        )
        method_output_contains(
            self,
            'page_preview',
            '/test-headline-of-many-characters.html" target="_blank">Page</a>',
        )

    def test_email_preview(self):
        method_output_contains(
            self,
            'email_preview',
            '<a href="',
        )
        method_output_contains(
            self,
            'email_preview',
            '/email-preview/test-list/',
        )
        method_output_contains(
            self,
            'email_preview',
            '">Email</a>',
        )

    def test_protocol_domain(self):
        site_instance = Site.objects.get(
            domain=self.profile_instance.domain,
        )
        with self.settings(
            SITE_ID=site_instance.id,
        ):
            method_output_equals(
                self,
                'protocol_domain',
                'http://127.0.0.1:8000',
            )

    def test_static_domain(self):
        site_instance = Site.objects.get(
            domain=self.profile_instance.domain,
        )
        with self.settings(
            STATIC_URL='/static/',
            SITE_ID=site_instance.id,
        ):
            method_output_equals(
                self,
                'static_domain',
                'http://127.0.0.1:8000',
            )

    def test_static_domain_http(self):
        site_instance = Site.objects.get(
            domain=self.profile_instance.domain,
        )
        with self.settings(
            STATIC_URL='http://www.example.com/static/',
            SITE_ID=site_instance.id,
        ):
            method_output_equals(
                self,
                'static_domain',
                '',
            )

    def test_media_domain(self):
        site_instance = Site.objects.get(
            domain=self.profile_instance.domain,
        )
        with self.settings(
            MEDIA_URL='/media/',
            SITE_ID=site_instance.id,
        ):
            method_output_equals(
                self,
                'media_domain',
                'http://127.0.0.1:8000',
            )

    def test_media_domain_http(self):
        site_instance = Site.objects.get(
            domain=self.profile_instance.domain,
        )
        with self.settings(
            MEDIA_URL='http://www.example.com/media/',
            SITE_ID=site_instance.id,
        ):
            method_output_equals(
                self,
                'media_domain',
                '',
            )


class EmailImageTests(MixinWrap.BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        email_instance = create_email()
        self.test_instance = email_instance.email_image()
        super().setUp()

    def test_str(self):
        method_output_equals(
            self,
            '__str__',
            'Test description',
        )

    def test_save(self):
        attribute_equals(
            self,
            {
                'output_width': 1080,
            },
        )


class EmailTrackerTests(MixinWrap.BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.test_instance = create_tracker()
        super().setUp()

    def test_send_complete_string(self):
        method_output_equals(
            self,
            'send_complete_string',
            localize(timezone.localtime(self.test_instance.send_complete)),
        )


class MonthlyStatTests(MixinWrap.BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.test_instance = create_stats()
        super().setUp()

    def test_month_and_year(self):
        method_output_equals(
            self,
            'month_and_year',
            'January 2020',
        )

    def test_str(self):
        method_output_equals(
            self,
            '__str__',
            'January 2020',
        )

    def test_stat_table(self):
        method_output_contains(
            self,
            'stat_table',
            '<table id="emailer_table">',
        )
        method_output_contains(
            self,
            'stat_table',
            'Test stat data',
        )
        method_output_contains(
            self,
            'stat_table',
            '</table>',
        )
