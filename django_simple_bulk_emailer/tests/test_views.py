from unittest.mock import (
    patch,
)


from django.test import (
    TestCase,
)


from django_simple_bulk_emailer.views import (
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


from .functions import (
    attribute_equals,
    check_email,
    check_http_response,
    check_not_found,
    check_permission,
    check_quantity_email_sent,
    check_subscriber_attributes,
    check_subscriber_count,
    check_subscription_count,
    check_subscriber_subscription_state,
    clear_data_and_files,
    remove_subscriber,
    create_email,
    create_request_response,
    create_site_profile,
    create_subscriber,
    create_subscription,
    create_tracker,
    create_subscriber_subscription_state,
    create_user,
    fake_now,
    subscriber_exists,
)


class MixinWrap:
    class BaseMixin(TestCase):
        longMessage = False

        def setUp(self):
            self.profile_instance = create_site_profile()
            self.test_view = eval(self.view_name)
            super().setUp()

        def tearDown(self):
            clear_data_and_files()
            super().tearDown()


class GetSubscriptionsTests(MixinWrap.BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.view_name = 'get_subscriptions'
        self.kwargs = {
        }
        self.time_dict = {
            'seconds': 1,
        }
        create_subscriber()
        super().setUp()

    def test_get(self):
        create_request_response(
            self,
            'get',
        )
        check_subscriber_count(
            self,
            1,
        )
        check_quantity_email_sent(
            self,
            0,
        )
        check_http_response(
            self,
            form_load=True,
            true_strings=[
                'To subscribe or manage your subscriptions, submit your email address.',
            ],
            false_strings=[
                'Thank you. An email with instructions has been sent to the address provided.',
            ],
        )

    def test_post_new_subscriber(self):
        test_address = 'new@example.com'
        self.data = {
            'subscriber_email': test_address,
        }
        create_request_response(
            self,
            'post',
            time_dict=self.time_dict
        )
        check_subscriber_count(
            self,
            2,
        )
        subscriber_exists(
            self,
            test_address,
            True,
        )
        check_quantity_email_sent(
            self,
            1,
        )
        check_email(
            self,
            subject='Manage your email subscriptions',
            text_strings=[
                'You can select your email subscriptions',
            ],
            html_strings=[
                '<!DOCTYPE html>',
            ],
        )
        check_http_response(
            self,
            true_strings=[
                'Thank you. An email with instructions has been sent to the address provided.',
            ],
            false_strings=[
                'To subscribe or manage your subscriptions, submit your email address.',
            ],
        )

    def test_post_existing_subscriber(self):
        test_address = 'example@example.com'
        self.data = {
            'subscriber_email': test_address,
        }
        create_request_response(
            self,
            'post',
            time_dict=self.time_dict
        )
        subscriber_exists(
            self,
            test_address,
            True,
        )
        check_subscriber_count(
            self,
            1,
        )
        check_quantity_email_sent(
            self,
            1,
        )
        check_email(
            self,
            subject='Manage your email subscriptions',
            text_strings=[
                'You can select your email subscriptions',
            ],
            html_strings=[
                '<!DOCTYPE html>',
            ],
        )
        check_http_response(
            self,
            true_strings=[
                'Thank you. An email with instructions has been sent to the address provided.',
            ],
            false_strings=[
                'To subscribe or manage your subscriptions, submit your email address.',
            ],
        )

    def test_post_invalid_email(self):
        test_address = 'invalid_example.com'
        self.data = {
            'subscriber_email': test_address,
        }
        create_request_response(
            self,
            'post',
            time_dict=self.time_dict
        )
        subscriber_exists(
            self,
            test_address,
            False,
        )
        check_subscriber_count(
            self,
            1,
        )
        check_quantity_email_sent(
            self,
            0,
        )
        check_http_response(
            self,
            form_load=True,
            true_strings=[
                'To subscribe or manage your subscriptions, submit your email address.',
            ],
            false_strings=[
                'Thank you. An email with instructions has been sent to the address provided.',
            ],
        )

    def test_post_fast_submit(self):
        test_address = 'fast@example.com'
        self.data = {
            'subscriber_email': test_address,
        }
        create_request_response(
            self,
            'post',
            time_dict={
                'seconds': 0,
            }
        )
        subscriber_exists(
            self,
            test_address,
            False,
        )
        check_subscriber_count(
            self,
            1,
        )
        check_quantity_email_sent(
            self,
            0,
        )
        check_http_response(
            self,
            true_strings=[
                'Thank you. An email with instructions has been sent to the address provided.',
            ],
            false_strings=[
                'To subscribe or manage your subscriptions, submit your email address.',
            ],
        )

    def test_post_honeypot_content(self):
        test_address = 'honeypot@example.com'
        self.data = {
            'subscriber_email': test_address,
            'email': test_address,
        }
        create_request_response(
            self,
            'post',
            time_dict=self.time_dict
        )
        subscriber_exists(
            self,
            test_address,
            False,
        )
        check_subscriber_count(
            self,
            1,
        )
        check_quantity_email_sent(
            self,
            0,
        )
        check_http_response(
            self,
            true_strings=[
                'Thank you. An email with instructions has been sent to the address provided.',
            ],
            false_strings=[
                'To subscribe or manage your subscriptions, submit your email address.',
            ],
        )


class ManageSubscriptionsTests(MixinWrap.BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.subscriber = create_subscriber()
        self.subscription_one = create_subscription(list_name='List One')
        self.subscription_two = create_subscription(list_name='List Two')
        self.subscriber.subscriptions.add(self.subscription_one)
        self.view_name = 'manage_subscriptions'
        self.kwargs = {
            'subscriber_key': self.subscriber.subscriber_key,
        }
        super().setUp()

    def test_get_valid_key(self):
        create_request_response(
            self,
            'get',
        )
        check_http_response(
            self,
            true_strings=[
                'First name:',
                'name="first_name" value="Anonymous"',
                'name="last_name" value="Subscriber"',
                'name="subscriber_email" value="example@example.com"',
                'List One',
                'List Two',
                '" checked> List One',
                '"> List Two',
            ],
            false_strings=[
                'The access link is invalid or has expired.',
                '"> List One',
                '" checked> List Two',
            ],
        )

    def test_get_invalid_key(self):
        self.kwargs['subscriber_key'] = 'InvalidSubscriberKey'
        create_request_response(
            self,
            'get',
        )
        check_http_response(
            self,
            true_strings=[
                'The access link is invalid or has expired.',
                '/subscriptions/subscribe/">',
            ],
            false_strings=[
                'First name:',
            ],
        )

    def test_post_unsubscribe_all(self):
        self.data = {
            'unsubscribe_all': 'Unsubscribe from all',
        }
        create_request_response(
            self,
            'post',
        )
        check_subscription_count(
            self,
            0,
        )
        check_http_response(
            self,
            true_strings=[
                'Thank you. Your changes have been saved.',
            ],
        )

    def test_post_valid_email(self):
        test_email = 'new@example.com'
        self.data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'subscriber_email': test_email,
            'subscription_choices': ['1', '2'],
        }
        create_request_response(
            self,
            'post',
        )
        check_subscription_count(
            self,
            2,
        )
        check_subscriber_attributes(
            self,
            test_email,
            self.data,
            True,
        )
        check_http_response(
            self,
            true_strings=[
                'Thank you. Your changes have been saved.',
            ],
        )

    def test_post_invalid_email(self):
        self.data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'subscriber_email': 'new_example.com',
            'subscription_choices': ['1', '2'],
        }
        create_request_response(
            self,
            'post',
        )
        check_subscription_count(
            self,
            1,
        )
        check_subscriber_attributes(
            self,
            'example@example.com',
            self.data,
            False,
        )
        check_http_response(
            self,
            true_strings=[
                'First name:',
                'name="first_name" value="Updated"',
                'name="last_name" value="Name"',
                'name="subscriber_email" value="example@example.com"',
                '" checked> List One',
                '" checked> List Two',
            ],
            false_strings=[
                'Thank you. Your changes have been saved.',
                '"> List One',
                '"> List Two',
            ],
        )


class QuickUnsubscribeTests(MixinWrap.BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.subscriber = create_subscriber()
        self.subscription_one = create_subscription(list_name='List One')
        self.subscription_two = create_subscription(list_name='List Two')
        self.subscriber.subscriptions.add(self.subscription_one)
        self.view_name = 'quick_unsubscribe'
        self.kwargs = {
            'list_slug': self.subscription_one.list_slug,
            'subscriber_key': self.subscriber.subscriber_key,
        }
        super().setUp()

    def test_get_valid(self):
        create_request_response(
            self,
            'get',
        )
        check_subscription_count(
            self,
            0,
        )
        check_http_response(
            self,
            true_strings=[
                'You have been unsubscribed from the List One email distribution list.',
                '/subscriptions/manage/',
            ],
            false_strings=[
                'The access link is invalid or has expired.',
            ],
        )

    def test_get_invalid_slug(self):
        self.kwargs['list_slug'] = 'InvalidListSlug'
        create_request_response(
            self,
            'get',
        )
        check_http_response(
            self,
            true_strings=[
                'The access link is invalid or has expired.',
                '/subscriptions/subscribe/">',
            ],
            false_strings=[
                'First name:',
            ],
        )

    def test_get_invalid_key(self):
        self.kwargs['subscriber_key'] = 'InvalidSubscriberKey'
        create_request_response(
            self,
            'get',
        )
        check_http_response(
            self,
            true_strings=[
                'The access link is invalid or has expired.',
                '/subscriptions/subscribe/">',
            ],
            false_strings=[
                'First name:',
            ],
        )


class EmailPreviewTests(MixinWrap.BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.bulk_email = create_email()
        self.view_name = 'email_preview'
        self.kwargs = {
            'list_slug': self.bulk_email.subscription_list.list_slug,
            'pk': self.bulk_email.pk,
        }
        super().setUp()

    def test_get_without_permission(self):
        self.user = create_user()
        check_permission(
            self,
            False,
        )

    def test_get_with_view_permission(self):
        self.user = create_user(
            permission_list=[
                'view_bulkemail',
            ],
        )
        create_request_response(
            self,
            'get',
        )
        check_http_response(
            self,
            true_strings=[
                'Sending history:',
                'Email has not been sent.',
                'Return to list',
                'Test headline of many characters',
                'img src="http://127.0.0.1:8000/media/images/',
                'width="500"',
                'alt="Test description"',
                'Test caption',
                'Test body text paragraph one.',
                'a href="http://127.0.0.1:8000/media/documents/temporary/test-title-',
                'Test title',
                'Test extra text',
                'a href="/mail_test/test-list/',
                '/test-headline-of-many-characters.html',
            ],
            false_strings=[
                'Send email',
                'Email currently is being sent.',
                'Send email again',
            ],
        )

    def test_get_with_change_permission(self):
        self.user = create_user(
            permission_list=[
                'change_bulkemail',
                'view_bulkemail',
            ],
        )
        create_request_response(
            self,
            'get',
        )
        check_http_response(
            self,
            true_strings=[
                'Sending history:',
                'Email has not been sent.',
                'Send email',
                'Return to list',
                'Test headline of many characters',
                'img src="http://127.0.0.1:8000/media/images/',
                'width="500"',
                'alt="Test description"',
                'Test caption',
                'Test body text paragraph one.',
                'a href="http://127.0.0.1:8000/media/documents/temporary/test-title-',
                'Test title',
                'Test extra text',
                'a href="/mail_test/test-list/',
                '/test-headline-of-many-characters.html',
            ],
            false_strings=[
                'Email currently is being sent.',
                'Send email again',
            ],
        )

    def test_get_invalid_list(self):
        self.user = create_user(
            permission_list=[
                'view_bulkemail',
            ],
        )
        self.kwargs = {
            'list_slug': 'invalid-slug',
            'pk': self.bulk_email.pk,
        }
        check_not_found(
            self,
            True,
        )

    def test_get_invalid_key(self):
        self.user = create_user(
            permission_list=[
                'view_bulkemail',
            ],
        )
        self.kwargs = {
            'list_slug': self.bulk_email.subscription_list.list_slug,
            'pk': 999,
        }
        check_not_found(
            self,
            True,
        )

    def test_post_return_list(self):
        self.data = {
            'return_list': 'Return to list',
        }
        self.user = create_user(
            permission_list=[
                'change_bulkemail',
                'view_bulkemail',
            ],
        )
        create_request_response(
            self,
            'post',
        )
        check_http_response(
            self,
            status_code=302,
            redirect_url='/admin/django_simple_bulk_emailer/bulkemail/',
        )

    def test_post_send_email(self):
        self.data = {
            'send_email': 'Send email',
        }
        self.user = create_user(
            permission_list=[
                'change_bulkemail',
                'view_bulkemail',
            ],
        )
        create_request_response(
            self,
            'post',
        )
        check_http_response(
            self,
            status_code=302,
            redirect_url='/admin/django_simple_bulk_emailer/bulkemail/',
        )
        self.bulk_email.refresh_from_db()
        self.test_instance = self.bulk_email
        attribute_equals(
            self,
            {
                'sendable': True,
                'sending': True,
                'sent': True,
            },
        )
        create_request_response(
            self,
            'get',
        )
        check_http_response(
            self,
            true_strings=[
                'Sending history:',
                'Email currently is being sent.',
                'Return to list',
                'Test headline of many characters',
                'img src="http://127.0.0.1:8000/media/images/',
                'width="500"',
                'alt="Test description"',
                'Test caption',
                'Test body text paragraph one.',
                'a href="http://127.0.0.1:8000/media/documents/temporary/test-title-',
                'Test title',
                'Test extra text',
                'a href="/mail_test/test-list/',
                '/test-headline-of-many-characters.html',
            ],
            false_strings=[
                'Email has not been sent.',
                'Send email',
                'Send email again',
            ],
        )
        self.bulk_email.sendable = False
        self.bulk_email.send_history = 'Test sending history'
        self.bulk_email.sending = False
        self.bulk_email.save()
        create_request_response(
            self,
            'get',
        )
        check_http_response(
            self,
            true_strings=[
                'Sending history:',
                'Test sending history',
                'Send email again',
                'Return to list',
                'Test headline of many characters',
                'img src="http://127.0.0.1:8000/media/images/',
                'width="500"',
                'alt="Test description"',
                'Test caption',
                'Test body text paragraph one.',
                'a href="http://127.0.0.1:8000/media/documents/temporary/test-title-',
                'Test title',
                'Test extra text',
                'a href="/mail_test/test-list/',
                '/test-headline-of-many-characters.html',
            ],
            false_strings=[
                'Email has not been sent.',
                'Email currently is being sent.',
                'Send email<',
            ],
        )


class ListViewTests(MixinWrap.BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.subscription = create_subscription()
        self.view_name = 'list_view'
        self.kwargs = {
            'list_slug': self.subscription.list_slug,
        }
        for i in range(1, 12):
            headline = 'Test headline number {}'.format(str(i))
            email = create_email(
                headline=headline,
                list_name=self.subscription.list_name,
                published=True,
            )
            self.email_class = email.__class__
        super().setUp()

    def test_get_invalid_list(self):
        self.kwargs['list_slug'] = 'invalid-slug'
        check_not_found(
            self,
            True,
        )

    def test_get_not_publicly_visible(self):
        self.subscription.publicly_visible = False
        self.subscription.save()
        check_not_found(
            self,
            True,
        )

    def test_get_not_use_pages(self):
        self.subscription.use_pages = False
        self.subscription.save()
        check_not_found(
            self,
            True,
        )

    def test_get_page_content_published(self):
        true_strings = [
            '<a href="/mail_test/subscriptions/subscribe/">',
            '<a href="?q=&amp;page=2">',
        ]
        for i in range(2, 12):
            headline = '>Test headline number {}<'.format(str(i))
            true_strings.append(headline)
        create_request_response(
            self,
            'get',
        )
        check_http_response(
            self,
            true_strings=true_strings,
            false_strings=[
                '>Test headline number 1<',
            ],
        )

    def test_get_page_content_unpublished(self):
        emails = self.email_class.objects.all()
        for email in emails:
            email.published = False
            email.save()
        true_strings = [
            '<a href="/mail_test/subscriptions/subscribe/">',
        ]
        false_strings = [
            '<a href="?q=&amp;page=',
        ]
        for i in range(1, 12):
            headline = '>Test headline number {}<'.format(str(i))
            false_strings.append(headline)
        create_request_response(
            self,
            'get',
        )
        check_http_response(
            self,
            true_strings=true_strings,
            false_strings=false_strings,
        )

    def test_get_pagination_page_two(self):
        true_strings = [
            '<a href="/mail_test/subscriptions/subscribe/">',
            '<a href="?q=&amp;page=1">',
            '>Test headline number 1<',
        ]
        false_strings = []
        for i in range(2, 12):
            headline = '>Test headline number {}<'.format(str(i))
            false_strings.append(headline)
        create_request_response(
            self,
            'get',
            page='2',
        )
        check_http_response(
            self,
            true_strings=true_strings,
            false_strings=false_strings,
        )

    def test_get_pagination_setting(self):
        with self.settings(
            EMAILER_PAGINATION=False,
        ):
            true_strings = [
                '<a href="/mail_test/subscriptions/subscribe/">',
            ]
            for i in range(1, 12):
                headline = '>Test headline number {}<'.format(str(i))
                true_strings.append(headline)
            create_request_response(
                self,
                'get',
            )
            check_http_response(
                self,
                true_strings=true_strings,
            )

    def test_get_pagination_results_setting(self):
        with self.settings(
            EMAILER_PAGINATION_RESULTS=5,
        ):
            true_strings = [
                '<a href="/mail_test/subscriptions/subscribe/">',
            ]
            for i in range(7, 12):
                headline = '>Test headline number {}<'.format(str(i))
                true_strings.append(headline)
            false_strings = [
            ]
            for i in range(1, 7):
                headline = '>Test headline number {}<'.format(str(i))
                false_strings.append(headline)
            create_request_response(
                self,
                'get',
            )
            check_http_response(
                self,
                true_strings=true_strings,
                false_strings=false_strings,
            )

    def test_get_pagination_not_integer(self):
        true_strings = [
            '<a href="/mail_test/subscriptions/subscribe/">',
            '<a href="?q=&amp;page=2">',
        ]
        for i in range(2, 12):
            headline = '>Test headline number {}<'.format(str(i))
            true_strings.append(headline)
        create_request_response(
            self,
            'get',
            page='invalid',
        )
        check_http_response(
            self,
            true_strings=true_strings,
            false_strings=[
                '>Test headline number 1<',
            ],
        )


class PageViewPreviewBase(MixinWrap.BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.email = create_email(published=True)
        self.subscription = self.email.subscription_list
        self.subscription_two = create_subscription(list_name='List Two')
        self.kwargs = {
            'list_slug': self.subscription.list_slug,
            'year': '2000',
            'month': '1',
            'day': '1',
            'pk': self.email.pk,
            'headline_slug': 'dummy-headline-slug',
        }
        super().setUp()


class PageViewTests(PageViewPreviewBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.view_name = 'page_view'
        super().setUp()

    def test_get_subscription_invalid_slug(self):
        self.kwargs['list_slug'] = 'invalid-slug'
        check_not_found(
            self,
            True,
        )

    def test_get_subscription_invalid_list(self):
        self.kwargs['list_slug'] = self.subscription_two.list_slug
        check_not_found(
            self,
            True,
        )

    def test_get_subscription_not_public(self):
        self.subscription.publicly_visible = False
        self.subscription.save()
        check_not_found(
            self,
            True,
        )

    def test_get_subscription_not_pages(self):
        self.subscription.use_pages = False
        self.subscription.save()
        check_not_found(
            self,
            True,
        )

    def test_get_page_published(self):
        create_request_response(
            self,
            'get',
        )
        check_http_response(
            self,
            true_strings=[
                'Test headline of many characters',
                '<p>Test body text paragraph one.</p><p>Test body text paragraph two.</p>',
                'Test caption',
                'Test description',
                'Test title',
                'Test extra text',
            ],
        )

    def test_get_page_unpublished(self):
        self.email.published = False
        self.email.save()
        check_not_found(
            self,
            True,
        )

    def test_get_subscription_invalid_pk(self):
        self.kwargs['pk'] = 999
        check_not_found(
            self,
            True,
        )

    def test_get_meta_tags(self):
        create_request_response(
            self,
            'get',
        )
        file_name = self.email.email_image().processed_file.name
        check_http_response(
            self,
            true_strings=[
                '<meta property="og:url" content="http://testserver/mail_test/test-list/2000/1/1/1/dummy-headline-slug.html">',
                '<meta property="og:type" content="article">',
                '<meta property="og:description" content="Test body text paragraph one.">',
                '<meta property="og:title" content="Test headline of many characters">',
                '<meta property="og:image" content="http://127.0.0.1:8000/media/{}">'.format(file_name),
                '<meta property="og:image:url" content="http://127.0.0.1:8000/media/{}">'.format(file_name),
                '<meta property="og:image:type" content="image/png">',
                '<meta property="og:image:width" content="1080">',
                '<meta property="og:image:height" content="1080">',
                '<meta property="og:image:alt" content="Test description">',
            ],
        )

    def test_get_default_image_settings(self):
        with self.settings(
            EMAILER_DEFAULT_IMAGE='test-default-image',
            EMAILER_DEFAULT_TYPE='test-default-type',
            EMAILER_DEFAULT_WIDTH='test-default-width',
            EMAILER_DEFAULT_HEIGHT='test-default-height',
            EMAILER_DEFAULT_ALT='test-default-alt',
        ):
            self.email.email_image().delete()
            create_request_response(
                self,
                'get',
            )
            check_http_response(
                self,
                true_strings=[
                    '<meta property="og:image" content="test-default-image">',
                    '<meta property="og:image:type" content="test-default-type">',
                    '<meta property="og:image:width" content="test-default-width">',
                    '<meta property="og:image:height" content="test-default-height">',
                    '<meta property="og:image:alt" content="test-default-alt">',
                ],
            )


class PagePreviewTests(PageViewPreviewBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.view_name = 'page_preview'
        super().setUp()

    def test_get_preview_without_permission(self):
        self.user = create_user()
        check_permission(
            self,
            False,
        )

    def test_get_preview_with_view_permission(self):
        self.user = create_user(
            permission_list=[
                'view_bulkemail',
            ],
        )
        check_permission(
            self,
            True,
        )

    def test_get_preview_unpublished(self):
        self.email.published = False
        self.email.save()
        self.user = create_user(
            permission_list=[
                'view_bulkemail',
            ],
        )
        check_permission(
            self,
            True,
        )


@patch(
    'django_simple_bulk_emailer.views.timezone.now',
    fake_now,
)
class OpenedEmailTests(MixinWrap.BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_year = fake_now().year,
        self.current_month = fake_now().month,

    def setUp(self):
        self.subscriber = create_subscriber()
        self.tracker = create_tracker()
        self.view_name = 'opened_email'
        self.kwargs = {
            'pk': self.tracker.pk,
            'subscriber_key': self.subscriber.subscriber_key,
        }
        self.image_dict = {
            'width': 1,
            'height': 1,
            'mode': 'RGBA',
            'format': 'PNG',
        }
        self.test_json = '{{"{}": [{}, {}]}}'.format(
            self.subscriber.subscriber_key,
            self.current_year[0],
            self.current_month[0],
        )
        super().setUp()

    def test_get_invalid_pk(self):
        self.kwargs['pk'] = 999
        create_request_response(
            self,
            'get',
        )
        check_http_response(
            self,
            image_dict=self.image_dict,
        )

    def test_get_no_existing_data(self):
        create_request_response(
            self,
            'get',
        )
        check_http_response(
            self,
            json=True,
            true_strings=[
                self.test_json,
            ],
            image_dict=self.image_dict,
        )

    def test_get_existing_data(self):
        mock_json = '{"test_key": "Test value"}'
        self.tracker.json_data = mock_json
        self.tracker.save()
        create_request_response(
            self,
            'get',
        )
        merged_json = '{}, {}'.format(
            mock_json[:-1],
            self.test_json[1:],
        )
        check_http_response(
            self,
            json=True,
            true_strings=[
                merged_json,
            ],
            false_strings=[
                self.test_json,
                mock_json,
            ],
            image_dict=self.image_dict,
        )


class MCSyncTests(MixinWrap.BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.view_name = 'mc_sync'
        self.kwargs = {}
        self.original_email = 'original@example.com'
        self.orignal_first_name = 'OriginalFirst'
        self.orignal_last_name = 'OriginalLast'
        self.updated_email = 'updated@example.com'
        self.updated_first_name = 'UpdatedFirst'
        self.updated_last_name = 'UpdatedLast'
        self.test_list_id = 'testaudienceid'
        self.subscription_one = create_subscription(
            list_name='List One',
            mc_sync=True,
            mc_list=self.test_list_id,
        )
        self.subscription_two = create_subscription(
            list_name='List Two',
        )
        self.data = {
            'data[list_id]': self.test_list_id,
            'data[email]': self.original_email,
            'data[merges][FNAME]': self.orignal_first_name,
            'data[merges][LNAME]': self.orignal_last_name,
        }
        self.subscriber_attributes = {
            'first_name': self.orignal_first_name,
            'last_name': self.orignal_last_name,
            'mc_email': self.original_email,
        }
        self.states_dict = {
            0: 'does not exist',
            1: 'exists with no subscriptions',
            2: 'exists with subscription one',
            3: 'exists with subscription two',
            4: 'exists with subscriptions one and two',
        }
        super().setUp()

    def test_post_subscribe(self):
        self.data['type'] = 'subscribe'
        state_comparisons = {
            0: 2,
            1: 2,
            2: 2,
            3: 4,
            4: 4,
        }
        for start_state in state_comparisons.keys():
            create_subscriber_subscription_state(
                self,
                self.original_email,
                self.orignal_first_name,
                self.orignal_last_name,
                start_state,
            )
            create_request_response(
                self,
                'post',
            )
            extra_text = " — state tested was '{}'".format(
                self.states_dict.get(
                    start_state,
                ),
            )
            check_subscriber_subscription_state(
                self,
                self.original_email,
                self.subscriber_attributes,
                state_comparisons.get(
                    start_state,
                ),
                extra_text=extra_text,
            )
            remove_subscriber(self.original_email)

    def test_post_unsubscribe(self):
        self.data['type'] = 'unsubscribe'
        state_comparisons = {
            0: 0,
            1: 1,
            2: 1,
            3: 3,
            4: 3,
        }
        for start_state in state_comparisons.keys():
            create_subscriber_subscription_state(
                self,
                self.original_email,
                self.orignal_first_name,
                self.orignal_last_name,
                start_state,
            )
            create_request_response(
                self,
                'post',
            )
            extra_text = " — state tested was '{}'".format(
                self.states_dict.get(
                    start_state,
                ),
            )
            check_subscriber_subscription_state(
                self,
                self.original_email,
                self.subscriber_attributes,
                state_comparisons.get(
                    start_state,
                ),
                extra_text=extra_text,
            )
            remove_subscriber(self.original_email)

    def test_post_cleaned(self):
        self.data = {
            'type': 'cleaned',
            'data[list_id]': self.test_list_id,
            'data[email]': self.original_email,
        }
        state_comparisons = {
            0: 0,
            1: 1,
            2: 1,
            3: 3,
            4: 3,
        }
        for start_state in state_comparisons.keys():
            create_subscriber_subscription_state(
                self,
                self.original_email,
                self.orignal_first_name,
                self.orignal_last_name,
                start_state,
            )
            create_request_response(
                self,
                'post',
            )
            extra_text = " — state tested was '{}'".format(
                self.states_dict.get(
                    start_state,
                ),
            )
            check_subscriber_subscription_state(
                self,
                self.original_email,
                self.subscriber_attributes,
                state_comparisons.get(
                    start_state,
                ),
                extra_text=extra_text,
            )
            remove_subscriber(self.original_email)

    def test_post_update_email(self):
        self.data = {
            'type': 'upemail',
            'data[list_id]': self.test_list_id,
            'data[new_email]': self.updated_email,
            'data[old_email]': self.original_email,
        }
        updated_subscriber_attributes = {
            'mc_email': self.updated_email,
        }
        original_state_comparisons = {
            0: 0,
            1: 0,
            2: 0,
            3: 0,
            4: 0,
        }
        combined_state_comparisons = {
            0: {
                0: 2,
                1: 2,
                2: 2,
                3: 4,
                4: 4,
            },
            1: {
                0: 2,
                1: 2,
                2: 2,
                3: 4,
                4: 4,
            },
            2: {
                0: 2,
                1: 2,
                2: 2,
                3: 4,
                4: 4,
            },
            3: {
                0: 4,
                1: 4,
                2: 4,
                3: 4,
                4: 4,
            },
            4: {
                0: 4,
                1: 4,
                2: 4,
                3: 4,
                4: 4,
            },
        }
        for original_start_state in original_state_comparisons.keys():
            updated_state_comparisons = combined_state_comparisons.get(
                original_start_state,
            )
            for updated_start_state in updated_state_comparisons.keys():
                create_subscriber_subscription_state(
                    self,
                    self.original_email,
                    self.orignal_first_name,
                    self.orignal_last_name,
                    original_start_state,
                )
                create_subscriber_subscription_state(
                    self,
                    self.updated_email,
                    self.orignal_first_name,
                    self.orignal_last_name,
                    updated_start_state,
                )
                create_request_response(
                    self,
                    'post',
                )
                extra_text = " — old state was '{}' and new state was '{}'".format(
                    self.states_dict.get(
                        original_start_state,
                    ),
                    self.states_dict.get(
                        updated_start_state,
                    ),
                )
                check_subscriber_subscription_state(
                    self,
                    self.original_email,
                    self.subscriber_attributes,
                    original_state_comparisons.get(
                        original_start_state,
                    ),
                    extra_text=extra_text,
                )
                check_subscriber_subscription_state(
                    self,
                    self.updated_email,
                    updated_subscriber_attributes,
                    updated_state_comparisons.get(
                        updated_start_state,
                    ),
                    extra_text=extra_text,
                )
                remove_subscriber(self.original_email)
                remove_subscriber(self.updated_email)

    def test_post_update_profile_existing(self):
        self.data = {
            'type': 'profile',
            'data[list_id]': self.test_list_id,
            'data[email]': self.original_email,
            'data[merges][FNAME]': self.updated_first_name,
            'data[merges][LNAME]': self.updated_last_name,
        }
        updated_subscriber_attributes = {
            'first_name': self.updated_first_name,
            'last_name': self.updated_last_name,
            'subscription_choices': [str(self.subscription_one.pk)],
        }
        create_subscriber(
            subscriber_email=self.original_email,
            first_name=self.orignal_first_name,
            last_name=self.orignal_last_name,
        )
        create_request_response(
            self,
            'post',
        )
        check_subscriber_attributes(
            self,
            self.original_email,
            updated_subscriber_attributes,
            True,
        )

    def test_post_update_profile_not_existing(self):
        self.data = {
            'type': 'profile',
            'data[list_id]': self.test_list_id,
            'data[email]': self.original_email,
            'data[merges][FNAME]': self.updated_first_name,
            'data[merges][LNAME]': self.updated_last_name,
        }
        updated_subscriber_attributes = {
            'first_name': self.updated_first_name,
            'last_name': self.updated_last_name,
            'subscription_choices': [str(self.subscription_one.pk)],
        }
        create_request_response(
            self,
            'post',
        )
        check_subscriber_attributes(
            self,
            self.original_email,
            updated_subscriber_attributes,
            True,
        )

    def test_get_redirect(self):
        create_request_response(
            self,
            'get',
        )
        check_http_response(
            self,
            status_code=302,
            redirect_url='/',
        )
