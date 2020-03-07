from django.test import (
    TestCase,
)


from .functions import (
    check_field_in_form,
    check_form_is_valid,
    clear_data_and_files,
    create_subscription,
)

from django_simple_bulk_emailer.forms import (
    GetSubscriberForm,
    ModifySubscriberForm,
)


class MixinWrap:
    class BaseMixin(TestCase):
        longMessage = False

        def tearDown(self):
            clear_data_and_files()
            super().tearDown()


class GetSubscriberFormTests(MixinWrap.BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.form_class = GetSubscriberForm
        self.data = {
            'subscriber_email': 'example@example.com',
        }
        super().setUp()

    def test_valid_subscriber_valid_email(self):
        check_form_is_valid(
            self,
            True,
        )

    def test_valid_subscriber_invalid_email(self):
        self.data['subscriber_email'] = 'example_example.com'
        check_form_is_valid(
            self,
            False,
        )

    def test_valid_honeypot_valid_email(self):
        self.data['email'] = 'example@example.com'
        check_form_is_valid(
            self,
            True,
        )

    def test_valid_honeypot_invalid_email(self):
        self.data['email'] = 'example_example.com'
        check_form_is_valid(
            self,
            False,
        )
    '''
    ReCaptcha-related code is not tested
    '''


class SubscriptionSelectorModifySubscriberFormBase(MixinWrap.BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.form_class = ModifySubscriberForm
        self.data = {
            'first_name': 'Test',
            'last_name': 'User',
            'subscriber_email': 'example@example.com',
        }
        super().setUp()


class SubscriptionSelectorTests(SubscriptionSelectorModifySubscriberFormBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def test_valid_public_subscriptions(self):
        subscription_one = create_subscription(
            list_name='List One',
        )
        subscription_two = create_subscription(
            list_name='List Two',
        )
        self.data['subscription_choices'] = [
            subscription_one.pk,
            subscription_two.pk,
        ]
        check_form_is_valid(
            self,
            True,
        )

    def test_valid_nonpublic_subscription(self):
        subscription_one = create_subscription(
            list_name='List One',
            publicly_visible=False,
        )
        subscription_two = create_subscription(
            list_name='List Two',
        )
        self.data['subscription_choices'] = [
            subscription_one.pk,
            subscription_two.pk,
        ]
        check_form_is_valid(
            self,
            False,
        )


class ModifySubscriberFormTests(SubscriptionSelectorModifySubscriberFormBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.excluded_data = {
            'subscriptions': [1],
            'subscriber_key': 'test_key',
            'mc_email': 'example@example.com',
            'mc_synced': True,
        }
        super().setUp()

    def test_valid_all_required_fields(self):
        check_form_is_valid(
            self,
            True,
        )

    def test_valid_invalid_email(self):
        self.data['subscriber_email'] = 'example_example.com'
        check_form_is_valid(
            self,
            False,
        )

    def test_valid_empty_required_field(self):
        for key, value in self.data.items():
            old_value = value
            self.data[key] = ''
            extra_text = " — the field being tested was '{}'".format(
                key,
            )
            check_form_is_valid(
                self,
                False,
                extra_text=extra_text,
            )
            self.data[key] = old_value

    def test_data_excluded_fields(self):
        for key, value in self.excluded_data.items():
            self.data[key] = value
            check_field_in_form(
                self,
                key,
                False,
            )
            del self.data[key]
