from datetime import (
    timedelta,
)
from unittest.mock import (
    patch,
)


from django.test import (
    TestCase,
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

from mailchimp3.mailchimpclient import (
    MailChimpError,
)


from .functions import (
    attribute_equals,
    call_test_command,
    check_attached_trackers,
    check_email,
    check_quantity_email_sent,
    check_quantity_trackers,
    check_site_profile,
    check_site_profile_count,
    clear_data_and_files,
    create_email,
    create_site,
    create_site_profile,
    create_subscriber,
    create_subscriber_subscription_state,
    create_subscription,
    create_subscription_email_state,
    create_stats,
    create_tracker,
    email_exists,
    fake_now,
    get_default_site,
    get_monthly_stat,
    get_tracker,
    html_contains,
    remove_subscriber,
    remove_subscription_and_emails,
    subscriber_exists,
)


class MixinWrap:
    class BaseMixin(TestCase):
        longMessage = False

        def tearDown(self):
            clear_data_and_files()
            super().tearDown()


class DeleteExpiredEmailsTests(MixinWrap.BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.test_command = 'delete_expired_emails'
        super().setUp()

    def test_correct_emails_deleted(self):
        with patch(
            'django_simple_bulk_emailer.management.commands.delete_expired_emails.timezone.now',
            fake_now,
        ):
            headline_today = 'Delete today'
            headline_yesterday = 'Delete yesterday'
            headline_tomorrow = 'Delete tomorrow'
            email_today = create_email(
                headline=headline_today,
            )
            email_yesterday = create_email(
                headline=headline_yesterday,
            )
            email_tomorrow = create_email(
                headline=headline_tomorrow,
            )
            today = fake_now()
            yesterday = today - timedelta(days=1)
            tomorrow = today + timedelta(days=1)
            email_today.deletion_date = today.date()
            email_today.save()
            email_yesterday.deletion_date = yesterday.date()
            email_yesterday.save()
            email_tomorrow.deletion_date = tomorrow.date()
            email_tomorrow.save()
            call_test_command(self)
            email_exists(
                self,
                headline_today,
                False,
            )
            email_exists(
                self,
                headline_yesterday,
                False,
            )
            email_exists(
                self,
                headline_tomorrow,
                True,
            )


class DeleteUnsubscribedUsersTests(MixinWrap.BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.test_command = 'delete_unsubscribed_users'
        super().setUp()

    def test_correct_subscribers_deleted(self):
        with patch(
            'django_simple_bulk_emailer.management.commands.delete_unsubscribed_users.timezone.now',
            fake_now,
        ):
            subscription = create_subscription()
            email_subscribed = 'subscribed@example.com'
            email_presubscribed = 'presubscribed@example.com'
            email_unsubscribed = 'unsubscribed@example.com'
            subscriber_subscribed = create_subscriber(
                subscriber_email=email_subscribed,
            )
            subscriber_subscribed.subscriptions.add(subscription)
            subscriber_presubscribed = create_subscriber(
                subscriber_email=email_presubscribed,
            )
            subscriber_unsubscribed = create_subscriber(
                subscriber_email=email_unsubscribed,
            )
            subscriber_unsubscribed.created = fake_now() - timedelta(days=1)
            subscriber_unsubscribed.save()
            call_test_command(self)
            subscriber_exists(
                self,
                email_subscribed,
                True,
            )
            subscriber_exists(
                self,
                email_presubscribed,
                True,
            )
            subscriber_exists(
                self,
                email_unsubscribed,
                False,
            )


class ImportSitesTests(MixinWrap.BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.test_command = 'import_sites'
        super().setUp()

    def test_default_site(self):
        test_site = get_default_site()
        test_dict = {
            'domain': test_site.domain,
            'name': test_site.name,
        }
        call_test_command(self)
        check_site_profile_count(
            self,
            1,
        )
        check_site_profile(
            self,
            test_site,
            test_dict,
        )

    def test_additional_site(self):
        test_site = create_site()
        test_dict = {
            'domain': test_site.domain,
            'name': test_site.name,
        }
        call_test_command(self)
        check_site_profile_count(
            self,
            2,
        )
        check_site_profile(
            self,
            test_site,
            test_dict,
        )


class SendBulkEmailTests(MixinWrap.BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.profile_instance = create_site_profile()
        self.test_command = 'send_bulk_email'
        self.list_one_name = 'List One'
        self.list_two_name = 'List Two'
        self.subscriber_one_email = 'subscriber_one@example.com'
        self.subscriber_two_email = 'subscriber_two@example.com'
        super().setUp()

    def test_number_emails_sent(self):
        print('Checking email sending management command under 1,600 scenarios. This could take several minutes.')
        for state_one in range(8):
            for state_two in range(8):
                for state_three in range(5):
                    for state_four in range(5):
                        list_states = {
                            0: 'does not exist',
                            1: 'exists with no emails',
                            2: 'exists with one email, not sendable',
                            3: 'exists with one email, sendable',
                            4: 'exists with two emails, none sendable',
                            5: 'exists with two emails, first sendable',
                            6: 'exists with two emails, second sendable',
                            7: 'exists with two emails, both sendable',
                        }
                        create_subscription_email_state(
                            self,
                            self.list_one_name,
                            state_one,
                        )
                        list_one_state = 'list one {}'.format(
                            list_states[state_one],
                        )
                        create_subscription_email_state(
                            self,
                            self.list_two_name,
                            state_two,
                        )
                        list_two_state = '; list two {}'.format(
                            list_states[state_two],
                        )
                        list_one_emails_marked_send = 0
                        list_two_emails_marked_send = 0
                        if state_one == 3 or state_one == 5 or state_one == 7:
                            list_one_emails_marked_send += 1
                        if state_one > 5:
                            list_one_emails_marked_send += 1
                        if state_two == 3 or state_two == 5 or state_two == 7:
                            list_two_emails_marked_send += 1
                        if state_two > 5:
                            list_two_emails_marked_send += 1
                        subscriber_states = {
                            0: 'does not exist',
                            1: 'exists with no subscriptions',
                            2: 'exists with subscription one',
                            3: 'exists with subscription two',
                            4: 'exists with subscriptions one and two',
                        }
                        create_subscriber_subscription_state(
                            self,
                            self.subscriber_one_email,
                            'FirstOne',
                            'LastOne',
                            state_three,
                        )
                        subscriber_one_state = '; subscriber one {}'.format(
                            subscriber_states[state_three],
                        )
                        create_subscriber_subscription_state(
                            self,
                            self.subscriber_two_email,
                            'FirstTwo',
                            'LastTwo',
                            state_four,
                        )
                        subscriber_two_state = '; subscriber two {}'.format(
                            subscriber_states[state_four],
                        )
                        extra_text = ' — {}{}{}{}'.format(
                            list_one_state,
                            list_two_state,
                            subscriber_one_state,
                            subscriber_two_state,
                        )
                        list_one_subscribers = 0
                        list_two_subscribers = 0
                        if state_three == 2 or state_three == 4:
                            list_one_subscribers += 1
                        if state_three == 3 or state_three == 4:
                            list_two_subscribers += 1
                        if state_four == 2 or state_four == 4:
                            list_one_subscribers += 1
                        if state_four == 3 or state_four == 4:
                            list_two_subscribers += 1
                        list_one_email_sent = list_one_emails_marked_send * list_one_subscribers
                        list_two_email_sent = list_two_emails_marked_send * list_two_subscribers
                        quantity_email_sent = list_one_email_sent + list_two_email_sent
                        for attempt in range(8):
                            call_test_command(self)
                        check_quantity_email_sent(
                            self,
                            quantity_email_sent,
                            clear_outbox=True,
                            extra_text=extra_text,
                        )
                        remove_subscriber(self.subscriber_one_email)
                        remove_subscriber(self.subscriber_two_email)
                        remove_subscription_and_emails(self.list_one_name)
                        remove_subscription_and_emails(self.list_two_name)

    def test_sort_order_subscription(self):
        self.subscription_one = create_subscription(
            list_name=self.list_one_name,
            sort_order=2,
        )
        self.subscription_two = create_subscription(
            list_name=self.list_two_name,
            sort_order=1,
        )
        body_text_one = 'List One body text'
        body_text_two = 'List Two body text'
        create_email(
            list_name=self.list_one_name,
            body_text=body_text_one,
            sendable=True,
        )
        create_email(
            list_name=self.list_two_name,
            body_text=body_text_two,
            sendable=True,
        )
        create_subscriber_subscription_state(
            self,
            self.subscriber_one_email,
            'Anonymous',
            'Subscriber',
            4,
        )
        call_test_command(self)
        check_email(
            self,
            text_strings=[
                body_text_two,
            ],
        )
        call_test_command(self)
        check_email(
            self,
            email_number=1,
            text_strings=[
                body_text_one,
            ],
        )

    def test_sort_order_updated(self):
        self.subscription_one = create_subscription(
            list_name=self.list_one_name,
        )
        body_text_one = 'Newer update body text'
        body_text_two = 'Older update body text'
        updated_email = create_email(
            list_name=self.list_one_name,
            body_text=body_text_one,
            sendable=True,
        )
        create_email(
            list_name=self.list_one_name,
            body_text=body_text_two,
            sendable=True,
        )
        updated_email.save()
        create_subscriber_subscription_state(
            self,
            self.subscriber_one_email,
            'Anonymous',
            'Subscriber',
            2,
        )
        call_test_command(self)
        check_email(
            self,
            text_strings=[
                body_text_two,
            ],
        )
        call_test_command(self)
        check_email(
            self,
            email_number=1,
            text_strings=[
                body_text_one,
            ],
        )

    def test_email_content(self):
        test_headline = 'Headline for testing email content'
        self.subscription_one = create_subscription(
            list_name=self.list_one_name,
        )
        create_email(
            headline=test_headline,
            list_name=self.list_one_name,
            sendable=True,
        )
        subscriber = create_subscriber_subscription_state(
            self,
            self.subscriber_one_email,
            'Anonymous',
            'Subscriber',
            2,
        )
        call_test_command(self)
        tracker = get_tracker(test_headline)
        tracking_url = reverse(
            'django_simple_bulk_emailer:opened_email',
            kwargs={
                'pk': tracker.pk,
                'subscriber_key': subscriber.subscriber_key,
            },
        )
        '''
        Checking email:
            * is correct instance
            * is using text and HTML templates correctly
            * has correct protocol_domain
            * has correct tracking image
        '''
        check_email(
            self,
            subject=test_headline,
            text_strings=[
                'To unsubscribe, go to:',
                'http://127.0.0.1:8000',
            ],
            html_strings=[
                '<!DOCTYPE html>',
                tracking_url,
            ],
        )

    def test_attributes_after_sending(self):
        create_subscription(
            list_name=self.list_one_name,
        )
        bulk_email = create_email(
            list_name=self.list_one_name,
            sendable=True,
        )
        call_test_command(self)
        bulk_email.refresh_from_db()
        self.test_instance = bulk_email
        attribute_equals(
            self,
            {
                'sendable': False,
                'sending': False,
            },
            command=True,
        )

    def test_send_history_string(self):
        with patch(
            'django_simple_bulk_emailer.management.commands.send_bulk_email.timezone.now',
            fake_now,
        ):
            create_subscription(
                list_name=self.list_one_name,
            )
            bulk_email = create_email(
                list_name=self.list_one_name,
                sendable=True,
            )
            call_test_command(self)
            bulk_email.refresh_from_db()
            completed_string = '<ul><li>Completed: {}'.format(
                localize(timezone.localtime(fake_now())),
            )
            list_name_string = '<ul><li>Sent to: {}</li></ul></li></ul>'.format(
                self.list_one_name,
            )
            html_contains(
                self,
                bulk_email.send_history,
                true_strings=[
                    completed_string,
                    list_name_string,
                ],
            )

    def test_tracker_attributes(self):
        with patch(
            'django_simple_bulk_emailer.management.commands.send_bulk_email.timezone.now',
            fake_now,
        ):
            test_headline = 'Headline for testing tracker'
            self.subscription_one = create_subscription(
                list_name=self.list_one_name,
            )
            create_email(
                list_name=self.list_one_name,
                headline=test_headline,
                sendable=True,
            )
            create_subscriber_subscription_state(
                self,
                self.subscriber_one_email,
                'Anonymous',
                'Subscriber',
                2,
            )
            call_test_command(self)
            self.test_instance = get_tracker(test_headline)
            attribute_equals(
                self,
                {
                    'subject': test_headline,
                    'subscription_name': self.list_one_name,
                    'send_complete': fake_now(),
                    'number_sent': 1,
                },
                command=True,
            )


@patch(
    'django_simple_bulk_emailer.management.commands.sync_mailchimp.MailChimp',
)
class SyncMailChimpTests(MixinWrap.BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.test_command = 'sync_mailchimp'
        self.subscription_one = create_subscription(
            list_name='List_One',
            mc_sync=True,
            mc_list='test_list_one'
        )
        self.subscriber_one = create_subscriber()
        self.subscriber_one.subscriptions.add(
            self.subscription_one,
        )
        self.times_called = 0
        self.times_to_error = 0
        self.called_with_one = {}
        self.called_with_two = {}
        self.called_with_three = {}
        self.called_with_four = {}
        self.subscriber_hash_one = '23463b99b62a72f26ed677cc556c44e8'
        self.subscriber_hash_two = 'f6108c2a299984a59b3461a0907ef520'
        self.subscriber_hash_three = 'fb5de04bf1d2704933e3779e7ab79103'
        super().setUp()

    def generate_data(self, *args, subscriber=None, subscriber_hash=None, subscription=None):
        subscriber_data = {
            'list_id': subscription.mc_list,
            'subscriber_hash': subscriber_hash,
            'data': {
                'status_if_new': 'subscribed',
                'status': 'subscribed',
                'email_address': subscriber.subscriber_email,
                'merge_fields': {
                    'FNAME': subscriber.first_name,
                    'LNAME': subscriber.last_name,
                },
            },
        }
        return subscriber_data

    def generate_error_msg(self, *args, function_name=None, called_with=None, called_kwargs=None):
        error_msg = "MailChimp '{}' function should be called with:\n" \
                    "{}\n" \
                    "It was instead called with:\n" \
                    "{}\n".format(
                        function_name,
                        called_with,
                        called_kwargs,
                    )
        return error_msg

    def mock_create_or_update(self, *args, **kwargs):
        self.times_called += 1
        if self.times_called <= self.times_to_error:
            raise MailChimpError
        error_msg = self.generate_error_msg(
            function_name='create_or_update',
            called_with=self.called_with_one,
            called_kwargs=kwargs,
        )
        self.assertEqual(self.called_with_one, kwargs, error_msg)

    def mock_create_or_update_multiple(self, *args, **kwargs):
        self.times_called += 1
        if self.times_called == 1:
            error_msg = self.generate_error_msg(
                function_name='create_or_update',
                called_with=self.called_with_one,
                called_kwargs=kwargs,
            )
            self.assertEqual(self.called_with_one, kwargs, error_msg)
        if self.times_called == 2:
            error_msg = self.generate_error_msg(
                function_name='create_or_update',
                called_with=self.called_with_two,
                called_kwargs=kwargs,
            )
            self.assertEqual(self.called_with_two, kwargs, error_msg)
        if self.times_called == 3:
            error_msg = self.generate_error_msg(
                function_name='create_or_update',
                called_with=self.called_with_three,
                called_kwargs=kwargs,
            )
            self.assertEqual(self.called_with_three, kwargs, error_msg)
        if self.times_called == 4:
            error_msg = self.generate_error_msg(
                function_name='create_or_update',
                called_with=self.called_with_four,
                called_kwargs=kwargs,
            )
            self.assertEqual(self.called_with_four, kwargs, error_msg)

    def mock_update(self, *args, **kwargs):
        error_msg = self.generate_error_msg(
            function_name='update',
            called_with=self.update_called_with,
            called_kwargs=kwargs,
        )
        self.assertEqual(self.update_called_with, kwargs, error_msg)

    def check_subscriber_updated(self, *args, subscriber=None):
        subscriber.refresh_from_db()
        error_msg_one = "Subscriber 'subscriber_email' and 'mc_email' did not match after MailChimp sync"
        error_msg_two = "Subscriber 'mc_synced' returned 'False' after MailChimp sync"
        self.assertEqual(subscriber.subscriber_email, subscriber.mc_email, error_msg_one)
        self.assertEqual(subscriber.mc_synced, True, error_msg_two)

    def check_subscription_removed(self, *args, subscriber=None, subscription=None):
        subscriber.refresh_from_db()
        error_msg = "Subscriber still had subscription after MailChimp sync"
        self.assertNotEqual(subscriber.subscriptions, subscription, error_msg)

    def test_client_called_correctly(self, MockMailChimp):
        call_test_command(self)
        MockMailChimp.assert_called_once_with(
            mc_api='API_key',
            mc_user='username',
            timeout=30.0,
        )

    def test_new_subscriber_without_error(self, MockMailChimp):
        with patch.object(MockMailChimp().lists.members, 'create_or_update', new=self.mock_create_or_update):
            self.called_with_one = self.generate_data(
                self,
                subscriber=self.subscriber_one,
                subscriber_hash=self.subscriber_hash_one,
                subscription=self.subscription_one,
            )
            call_test_command(self)
            self.check_subscriber_updated(
                self,
                subscriber=self.subscriber_one,
            )

    def test_new_subscriber_with_error(self, MockMailChimp):
        with patch.object(MockMailChimp().lists.members, 'create_or_update', new=self.mock_create_or_update):
            self.called_with_one = self.generate_data(
                self,
                subscriber=self.subscriber_one,
                subscriber_hash=self.subscriber_hash_one,
                subscription=self.subscription_one,
            )
            self.times_to_error = 1
            call_test_command(self)
            self.check_subscriber_updated(
                self,
                subscriber=self.subscriber_one,
            )

    def test_updated_subscriber_without_error(self, MockMailChimp):
        with patch.object(MockMailChimp().lists.members, 'create_or_update', new=self.mock_create_or_update):
            self.subscriber_one.first_name = 'Updated'
            self.subscriber_one.last_name = 'User'
            self.subscriber_one.subscriber_email = 'updated@example.com'
            self.subscriber_one.save()
            self.called_with_one = self.generate_data(
                self,
                subscriber=self.subscriber_one,
                subscriber_hash=self.subscriber_hash_one,
                subscription=self.subscription_one,
            )
            call_test_command(self)
            self.check_subscriber_updated(
                self,
                subscriber=self.subscriber_one,
            )
    
    def test_updated_subscriber_with_error(self, MockMailChimp):
        with patch.object(MockMailChimp().lists.members, 'create_or_update', new=self.mock_create_or_update):
            self.subscriber_one.first_name = 'Updated'
            self.subscriber_one.last_name = 'User'
            self.subscriber_one.subscriber_email = 'updated@example.com'
            self.subscriber_one.save()
            self.times_to_error = 1
            self.called_with_one = self.generate_data(
                self,
                subscriber=self.subscriber_one,
                subscriber_hash=self.subscriber_hash_two,
                subscription=self.subscription_one,
            )
            call_test_command(self)
            self.check_subscriber_updated(
                self,
                subscriber=self.subscriber_one,
            )

    def test_subscriber_with_two_errors(self, MockMailChimp):
        with patch.object(MockMailChimp().lists.members, 'create_or_update', new=self.mock_create_or_update):
            self.times_to_error = 2
            call_test_command(self)
            self.check_subscriber_updated(
                self,
                subscriber=self.subscriber_one,
            )
            self.check_subscription_removed(
                self,
                subscriber=self.subscriber_one,
                subscription=self.subscription_one,
            )

    def test_subscriber_unsubscribed(self, MockMailChimp):
        self.subscriber_one.subscriptions.clear()
        with patch.object(MockMailChimp().lists.members, 'create_or_update', new=self.mock_create_or_update):
            with patch.object(MockMailChimp().lists.members, 'update', new=self.mock_update):
                self.called_with_one = self.generate_data(
                    self,
                    subscriber=self.subscriber_one,
                    subscriber_hash=self.subscriber_hash_one,
                    subscription=self.subscription_one,
                )
                self.update_called_with = {
                    'list_id': self.subscription_one.mc_list,
                    'subscriber_hash': self.subscriber_hash_one,
                    'data': {
                        'status': 'unsubscribed',
                    },
                }
                call_test_command(self)
                self.check_subscriber_updated(
                    self,
                    subscriber=self.subscriber_one,
                )

    def test_multiples(self, MockMailChimp):
        self.subscription_two = create_subscription(
            list_name='List Two',
            mc_sync=True,
            mc_list='test_list_two'
        )
        self.subscriber_two = create_subscriber(
            subscriber_email='second@example.com',
            first_name='Second',
            last_name='User',
        )
        self.subscriber_one.subscriptions.add(self.subscription_two)
        self.subscriber_two.subscriptions.add(self.subscription_one, self.subscription_two)
        with patch.object(MockMailChimp().lists.members, 'create_or_update', new=self.mock_create_or_update_multiple):
            self.called_with_one = self.generate_data(
                self,
                subscriber=self.subscriber_one,
                subscriber_hash=self.subscriber_hash_one,
                subscription=self.subscription_one,
            )
            self.called_with_two = self.generate_data(
                self,
                subscriber=self.subscriber_one,
                subscriber_hash=self.subscriber_hash_one,
                subscription=self.subscription_two,
            )
            self.called_with_three = self.generate_data(
                self,
                subscriber=self.subscriber_two,
                subscriber_hash=self.subscriber_hash_three,
                subscription=self.subscription_one,
            )
            self.called_with_four = self.generate_data(
                self,
                subscriber=self.subscriber_two,
                subscriber_hash=self.subscriber_hash_three,
                subscription=self.subscription_two,
            )
            call_test_command(self)
            self.check_subscriber_updated(
                self,
                subscriber=self.subscriber_one,
            )
            self.check_subscriber_updated(
                self,
                subscriber=self.subscriber_two,
            )

'''
Testing for MailChimp does not check every combination of subscription and subscriber but covers most scenarios.
'''


@patch(
    'django_simple_bulk_emailer.management.commands.update_email_stats.timezone.now',
    fake_now,
)
class UpdateEmailStatsTests(MixinWrap.BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.test_command = 'update_email_stats'
        self.list_one_name = 'List One'
        self.list_two_name = 'List Two'
        super().setUp()

    def test_stat_object_created(self):
        call_test_command(self)
        self.test_instance = get_monthly_stat(
            year_int=2020,
            month_int=1,
        )
        attribute_equals(
            self,
            {
                'stat_data': '',
            },
            command=True,
        )
        check_attached_trackers(
            self,
            count_dict={
                'current_trackers': 0,
                'older_trackers': 0,
            },
        )

    def test_stat_object_found(self):
        create_stats()
        call_test_command(self)
        self.test_instance = get_monthly_stat(
            year_int=2020,
            month_int=1,
        )
        attribute_equals(
            self,
            {
                'stat_data': '',
            },
            command=True,
        )
        check_attached_trackers(
            self,
            count_dict={
                'current_trackers': 0,
                'older_trackers': 0,
            },
        )

    def test_outdated_tracker_deleted(self):
        create_tracker(
            send_complete=fake_now(
                year=2019,
                month=10,
            ),
        )
        call_test_command(self)
        check_quantity_trackers(
            self,
            0,
        )

    def test_tracking_months_setting(self):
        with self.settings(
            EMAILER_TRACKING_MONTHS=4,
        ):
            create_tracker(
                send_complete=fake_now(
                    year=2019,
                    month=10,
                ),
            )
            call_test_command(self)
            check_quantity_trackers(
                self,
                1,
            )

    def test_correct_trackers_attached(self):
        current_subject = 'Current tracker subject'
        create_tracker(
            subject=current_subject,
            send_complete=fake_now(
                year=2020,
                month=1,
            ),
            json_data='{"test_key": [2020, 1]}',
        )
        older_subject = 'Older tracker subject'
        create_tracker(
            subject=older_subject,
            send_complete=fake_now(
                year=2019,
                month=12,
            ),
            json_data='{"test_key": [2020, 1]}',
        )
        irrelevant_subject = 'Irrelevant tracker subject'
        create_tracker(
            subject=irrelevant_subject,
            send_complete=fake_now(
                year=2020,
                month=1,
            ),
            json_data='{"test_key": [2019, 12]}',
        )
        call_test_command(self)
        self.test_instance = get_monthly_stat(
            year_int=2020,
            month_int=1,
        )
        current_set = get_tracker(
            current_subject,
            first=False,
        )
        older_set = get_tracker(
            older_subject,
            first=False,
        )
        check_attached_trackers(
            self,
            count_dict={
                'current_trackers': 1,
                'older_trackers': 1,
            },
            set_dict={
                'current_trackers': current_set,
                'older_trackers': older_set,
            },
        )

    def test_ordered_subscription_list(self):
        create_tracker(
            subscription_name=self.list_one_name,
            send_complete=fake_now(
                year=2020,
                month=1,
            ),
            json_data='{"test_key": [2020, 1]}',
        )
        create_tracker(
            subscription_name=self.list_one_name,
            send_complete=fake_now(
                year=2020,
                month=1,
            ),
            json_data='{"test_key": [2020, 1]}',
        )
        create_tracker(
            subscription_name=self.list_two_name,
            send_complete=fake_now(
                year=2020,
                month=1,
            ),
            json_data='{"test_key": [2020, 1]}',
        )
        create_tracker(
            subscription_name=self.list_two_name,
            send_complete=fake_now(
                year=2020,
                month=1,
            ),
            json_data='{"test_key": [2020, 1]}',
        )
        call_test_command(self)
        self.test_instance = get_monthly_stat(
            year_int=2020,
            month_int=1,
        )
        test_string_list = self.test_instance.stat_data.split('<tr')
        html_contains(
            self,
            test_string_list[1],
            true_strings=[
                self.list_one_name,
            ],
        )
        html_contains(
            self,
            test_string_list[5],
            true_strings=[
                self.list_two_name,
            ],
        )
        html_contains(
            self,
            self.test_instance.stat_data,
            false_strings=[
                'Older emails',
            ],
        )

    def test_ordered_subscription_list_with_older(self):
        test_list_one_name = 'X-Ray List'
        test_list_two_name = 'Zebra List'
        create_tracker(
            subscription_name=test_list_one_name,
            send_complete=fake_now(
                year=2020,
                month=1,
            ),
            json_data='{"test_key": [2020, 1]}',
        )
        create_tracker(
            subscription_name=test_list_two_name,
            send_complete=fake_now(
                year=2020,
                month=1,
            ),
            json_data='{"test_key": [2020, 1]}',
        )
        create_tracker(
            send_complete=fake_now(
                year=2019,
                month=12,
            ),
            json_data='{"test_key": [2020, 1]}',
        )
        call_test_command(self)
        self.test_instance = get_monthly_stat(
            year_int=2020,
            month_int=1,
        )
        test_string_list = self.test_instance.stat_data.split('<tr')
        html_contains(
            self,
            test_string_list[1],
            true_strings=[
                test_list_one_name,
            ],
        )
        html_contains(
            self,
            test_string_list[4],
            true_strings=[
                test_list_two_name,
            ],
        )
        html_contains(
            self,
            test_string_list[7],
            true_strings=[
                'Older emails',
            ],
        )

    def test_stats_html_content(self):
        current_subject_one = 'Current test email one'
        create_tracker(
            subject=current_subject_one,
            subscription_name=self.list_one_name,
            send_complete=fake_now(
                year=2020,
                month=1,
            ),
            number_sent=2,
            json_data='{"test_key": [2020, 1]}',
        )
        current_subject_two = 'Current test email two'
        create_tracker(
            subject=current_subject_two,
            subscription_name=self.list_one_name,
            send_complete=fake_now(
                year=2020,
                month=1,
            ),
            number_sent=4,
            json_data='{"test_key_one": [2020, 1], "test_key_two": [2020, 1], "test_key_three": [2020, 1]}',
        )
        older_subject_one = 'Older test email one'
        create_tracker(
            subject=older_subject_one,
            subscription_name=self.list_two_name,
            send_complete=fake_now(
                year=2019,
                month=11,
            ),
            number_sent=4,
            json_data='{"test_key": [2020, 1]}',
        )
        older_subject_two = 'Older test email two'
        create_tracker(
            subject=older_subject_two,
            subscription_name=self.list_two_name,
            send_complete=fake_now(
                year=2019,
                month=12,
            ),
            number_sent=3,
            json_data='{"test_key_one": [2020, 1], "test_key_two": [2020, 1], "test_key_three": [2020, 1]}',
        )
        call_test_command(self)
        self.test_instance = get_monthly_stat(
            year_int=2020,
            month_int=1,
        )
        test_string_list = self.test_instance.stat_data.split('<tr')
        html_contains(
            self,
            test_string_list[1],
            true_strings=[
                ' id="emailer_title_row">',
                '<td>&nbsp;</td>',
                '<td>List One</td>',
                '<td id="emailer_numerical">Sent</td>',
                '<td id="emailer_numerical">Opens</td>',
                '<td></td>',
                '</tr>',
            ],
        )
        html_contains(
            self,
            test_string_list[2],
            true_strings=[
                ' id="emailer_row_odd">',
                '<td id="emailer_numerical">1.</td>',
                '<td>{}<br>Jan. 1, 2020, midnight</td>'.format(
                    current_subject_two,
                ),
                '<td id="emailer_numerical">4</td>',
                '<td id="emailer_numerical">3</td>',
                '<td id="emailer_numerical">75.0%</td>',
                '</tr>',
            ],
        )
        html_contains(
            self,
            test_string_list[3],
            true_strings=[
                ' id="emailer_row_even">',
                '<td id="emailer_numerical">2.</td>',
                '<td>{}<br>Jan. 1, 2020, midnight</td>'.format(
                    current_subject_one,
                ),
                '<td id="emailer_numerical">2</td>',
                '<td id="emailer_numerical">1</td>',
                '<td id="emailer_numerical">50.0%</td>',
                '</tr>',
            ],
        )
        html_contains(
            self,
            test_string_list[4],
            true_strings=[
                ' id="emailer_title_row">',
                '<td><br><br></td>',
                '<td id="emailer_numerical">Totals:<br><br></td>',
                '<td id="emailer_numerical">6<br><br></td>',
                '<td id="emailer_numerical">4<br><br></td>',
                '<td id="emailer_numerical">66.7%<br><br></td> ',
                '</tr>',
            ],
        )
        html_contains(
            self,
            test_string_list[5],
            true_strings=[
                ' id="emailer_title_row">',
                '<td>&nbsp;</td>',
                '<td>Older emails</td>',
                '<td id="emailer_numerical">Sent</td>',
                '<td id="emailer_numerical">Opens</td>',
                '<td></td>',
                '</tr>',
            ],
        )
        html_contains(
            self,
            test_string_list[6],
            true_strings=[
                ' id="emailer_row_odd">',
                '<td id="emailer_numerical">1.</td>',
                '<td>{}<br>Dec. 1, 2019, midnight</td>'.format(
                    older_subject_two,
                ),
                '<td id="emailer_numerical">3</td>',
                '<td id="emailer_numerical">3</td>',
                '<td id="emailer_numerical">100.0%</td>',
                '</tr>',
            ],
        )
        html_contains(
            self,
            test_string_list[7],
            true_strings=[
                ' id="emailer_row_even">',
                '<td id="emailer_numerical">2.</td>',
                '<td>{}<br>Nov. 1, 2019, midnight</td>'.format(
                    older_subject_one,
                ),
                '<td id="emailer_numerical">4</td>',
                '<td id="emailer_numerical">1</td>',
                '<td id="emailer_numerical">25.0%</td>',
                '</tr>',
            ],
        )
        html_contains(
            self,
            test_string_list[8],
            true_strings=[
                ' id="emailer_title_row">',
                '<td><br><br></td>',
                '<td id="emailer_numerical">Totals:<br><br></td>',
                '<td id="emailer_numerical">7<br><br></td>',
                '<td id="emailer_numerical">4<br><br></td>',
                '<td id="emailer_numerical">57.1%<br><br></td> ',
                '</tr>',
            ],
        )
