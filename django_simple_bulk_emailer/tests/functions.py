from datetime import (
    datetime,
    timedelta,
    timezone,
)
from io import (
    BytesIO,
)


from django.contrib.auth.models import (
    Permission,
    User,
)
from django.contrib.sessions.middleware import (
    SessionMiddleware,
)
from django.contrib.sites.models import (
    Site,
)
from django.core import (
    mail,
)
from django.core.exceptions import (
    ObjectDoesNotExist,
    PermissionDenied,
)
from django.core.files.uploadedfile import (
    SimpleUploadedFile,
)
from django.core.management import (
    call_command,
)
from django.http import (
    Http404,
)
from django.test import (
    RequestFactory,
)
from django.urls import (
    reverse,
)
from django.utils import (
    timezone as django_timezone,
)


from PIL import (
    Image,
)


from django_simple_bulk_emailer.models import (
    BulkEmail,
    EmailDocument,
    EmailImage,
    EmailTracker,
    MonthlyStat,
    SiteProfile,
    Subscriber,
    Subscription,
)


def get_default_site():
    return Site.objects.first()


def get_tracker(subject, first=True):
    tracker_set = EmailTracker.objects.filter(
        subject=subject,
    )
    if first:
        return tracker_set.first()
    else:
        return tracker_set


def get_monthly_stat(year_int, month_int):
    return MonthlyStat.objects.get(
        year_int=year_int,
        month_int=month_int,
    )


def fake_now(year=2020, month=1):
    return datetime(year, month, 1, tzinfo=timezone.utc)


def create_site():
    site_profile = Site.objects.create(
        domain='second.example.com',
        name='Second test site',
    )
    return site_profile


def create_site_profile():
    site_profile = SiteProfile.objects.create(
        protocol='http://',
        domain='127.0.0.1:8000',
        name='Development server',
    )
    return site_profile


def create_subscription(list_name='Test list', publicly_visible=True, mc_sync=False, mc_list='test', sort_order=0):
    subscription = Subscription.objects.create(
        list_name=list_name,
        descriptive_text='Test list description',
        publicly_visible=publicly_visible,
        use_pages=True,
        mc_sync=mc_sync,
        mc_list=mc_list,
        sort_order=sort_order,
    )
    return subscription


def create_subscriber(subscriber_email='example@example.com', first_name='Anonymous', last_name='Subscriber'):
    subscriber = Subscriber.objects.create(
        subscriber_email=subscriber_email,
        first_name=first_name,
        last_name=last_name,
    )
    return subscriber


def create_image_file():
    temp_handle = BytesIO()
    image_file = Image.new(
        'RGB',
        (72, 72),
        (0, 0, 255),
    )
    image_file.save(
        temp_handle,
        'jpeg',
    )
    temp_handle.seek(0)
    return SimpleUploadedFile(
        'test_image.jpeg',
        temp_handle.read(),
        'image/jpeg',
    )


def create_document_file():
    return SimpleUploadedFile(
            'test_file.pdf',
            'test file content'.encode(),
            'application/pdf',
        )


def create_email(headline=None, list_name=None, body_text=None, published=False, sendable=False):
    if not headline:
        headline = 'Test headline of many characters'
    if not body_text:
        body_text = '<p>Test body text paragraph one.</p><p>Test body text paragraph two.</p>'
    if list_name:
        subscription_list = Subscription.objects.filter(
            list_name=list_name,
        ).first()
    else:
        subscription_list = create_subscription()
    bulk_email = BulkEmail.objects.create(
        subscription_list=subscription_list,
        headline=headline,
        body_text=body_text,
        published=published,
        sendable=sendable,
    )
    EmailImage.objects.create(
        bulk_email=bulk_email,
        caption='Test caption',
        description='Test description',
        image_width=1080,
        saved_file=create_image_file(),
    )
    EmailDocument.objects.create(
        bulk_email=bulk_email,
        title='Test title',
        extra_text='Test extra text',
        saved_file=create_document_file()
    )
    return bulk_email


def create_tracker(subject='Test email subject', subscription_name='Test subscription', send_complete=django_timezone.now(), number_sent=0, json_data=None):
    if json_data is None:
        json_data = {}
    tracker = EmailTracker.objects.create(
        subject=subject,
        subscription_name=subscription_name,
        send_complete=send_complete,
        number_sent=number_sent,
        json_data=json_data,
    )
    return tracker


def create_stats(year_int=2020, month_int=1, stat_data='Test stat data'):
    stats = MonthlyStat.objects.create(
        year_int=year_int,
        month_int=month_int,
        stat_data=stat_data,
    )
    return stats


def create_user(permission_list=None):
    user = User.objects.create_user(
        username='test_user',
        password='test_password',
    )
    if permission_list:
        user.is_staff = True
        user.save()
        for permission in permission_list:
            added_permission = Permission.objects.get(
                codename=permission,
            )
            user.user_permissions.add(added_permission)
    return user


def dummy_get_response(request):
    return None


def create_request_response(self, get_post, page='1', key='empty', time_dict=None):
    reverse_name = f'django_simple_bulk_emailer:{self.view_name}'
    with self.settings(
        SITE_ID=self.profile_instance.site_ptr.id,
    ):
        reverse_string = reverse(
            reverse_name,
            kwargs=self.kwargs,
        )
        if page != '1':
            reverse_string = f'{reverse_string}?page={page}'
        if key != 'empty':
            reverse_string = f'{reverse_string}?key={key}'
        if get_post == 'post':
            self.request = RequestFactory().post(
                reverse_string,
                self.data,
            )
        else:
            self.request = RequestFactory().get(
                reverse_string,
            )
        try:
            self.request.user = self.user
        except AttributeError:
            pass
        SessionMiddleware(dummy_get_response).process_request(self.request)
        if time_dict:
            load_time = django_timezone.now() - timedelta(**time_dict)
            self.request.session['form_load_time'] = load_time.timestamp()
            self.request.session.save()
        args = []
        for key, value in self.kwargs.items():
            args.append(value)
        self.response = self.test_view(
            self.request,
            *args,
        )


def create_subscriber_subscription_state(self, subscriber_email, first_name, last_name, state):
    """ """
    '''
    0: Does not exist
    1: Exists with no subscriptions
    2: Exists with subscription one
    3: Exists with subscription two
    4: Exists with subscriptions one and two
    '''
    if state != 0:
        subscriber = create_subscriber(
            subscriber_email=subscriber_email,
            first_name=first_name,
            last_name=last_name,
        )
        if state == 2 or state == 4:
            try:
                subscriber.subscriptions.add(self.subscription_one)
            except AttributeError:
                pass
        if state == 3 or state == 4:
            try:
                subscriber.subscriptions.add(self.subscription_two)
            except AttributeError:
                pass
        return subscriber


def create_subscription_email_state(self, list_name, state):
    """ """
    '''
    0: 'does not exist',
    1: 'exists with no emails',
    2: 'exists with one email, not sendable',
    3: 'exists with one email, sendable',
    4: 'exists with two emails, none sendable',
    5: 'exists with two emails, first sendable',
    6: 'exists with two emails, second sendable',
    7: 'exists with two emails, both sendable',
    '''
    if state != 0:
        subscription = create_subscription(
            list_name=list_name,
        )
        if list_name == self.list_one_name:
            self.subscription_one = subscription
        if list_name == self.list_two_name:
            self.subscription_two = subscription
        if state != 1:
            email_one = create_email(
                list_name=list_name,
            )
        if state > 3:
            email_two = create_email(
                list_name=list_name,
            )
        if state == 3 or state == 5 or state == 7:
            email_one.sendable = True
            email_one.save()
        if state > 5:
            email_two.sendable = True
            email_two.save()


def call_test_command(self):
    try:
        with self.settings(
                SITE_ID=self.profile_instance.site_ptr.id,
        ):
            call_command(
                self.test_command,
            )
    except AttributeError:
        call_command(
            self.test_command,
        )


def remove_subscriber(subscriber_email):
    try:
        subscriber = Subscriber.objects.get(
            subscriber_email=subscriber_email,
        )
        for subscription in subscriber.subscriptions.all():
            subscriber.subscriptions.remove(subscription)
        subscriber.delete()
    except ObjectDoesNotExist:
        pass


def remove_subscription_and_emails(list_name):
    try:
        subscription = Subscription.objects.get(
            list_name=list_name,
        )
        BulkEmail.objects.filter(
            subscription_list=subscription,
        ).delete()
        subscription.delete()
    except ObjectDoesNotExist:
        pass


def clear_data_and_files():
    BulkEmail.objects.all().delete()
    EmailTracker.objects.all().delete()
    MonthlyStat.objects.all().delete()
    SiteProfile.objects.all().delete()
    Subscription.objects.all().delete()
    Subscriber.objects.all().delete()


def attribute_equals(self, attr_dict, command=False):
    if command:
        inserted_text = f"command '{self.test_command}'"
    else:
        inserted_text = f"model '{self.test_instance.__class__.__name__}'"
    for key, value in attr_dict.items():
        error_msg = f"For {inserted_text}, the value of attribute '{key}' was not '{value}'"
        attr = getattr(self.test_instance, key)
        self.assertTrue(attr == value, error_msg)


def attribute_length_equals(self, attr_name, value):
    error_msg = f"For model '{self.test_instance.__class__.__name__}', the length of attribute '{attr_name}' was not '{value}'"
    attr = getattr(self.test_instance, attr_name)
    self.assertIs(len(attr), value, error_msg)


def method_output_equals(self, attr_name, value):
    error_msg = f"For model '{self.test_instance.__class__.__name__}', the output of method '{attr_name}' was not '{value}'"
    function = getattr(self.test_instance, attr_name)
    self.assertTrue(function() == value, error_msg)


def method_output_contains(self, attr_name, value):
    error_msg = f"For model '{self.test_instance.__class__.__name__}', the output of method '{attr_name}' did not contain '{value}'"
    function = getattr(self.test_instance, attr_name)
    self.assertIn(value, function(), error_msg)


def method_output_length_equals(self, attr_name, value):
    error_msg = f"For model '{self.test_instance.__class__.__name__}', the length of the output of method '{attr_name}' was not '{value}'"
    function = getattr(self.test_instance, attr_name)
    self.assertIs(len(function()), value, error_msg)


def email_exists(self, headline, boolean):
    error_msg_true = f"An email with headline '{headline}' does not exist"
    error_msg_false = f"An email with headline '{headline}' should not exist"
    try:
        bulk_email = BulkEmail.objects.get(
            headline=headline,
        )
    except ObjectDoesNotExist:
        bulk_email = BulkEmail.objects.none()
    if boolean:
        self.assertTrue(bulk_email, error_msg_true)
    else:
        self.assertFalse(bulk_email, error_msg_false)


def stats_exist(self, year_int, month_int, boolean):
    error_msg_true = f"Monthly stats with year '{str(year_int)}' and month '{str(month_int)}' do not exist"
    error_msg_false = f"Monthly stats with year '{str(year_int)}' and month '{str(month_int)}' should not exist"
    try:
        stats = MonthlyStat.objects.get(
            year_int=year_int,
            month_int=month_int,
        )
    except ObjectDoesNotExist:
        stats = MonthlyStat.objects.none()
    if boolean:
        self.assertTrue(stats, error_msg_true)
    else:
        self.assertFalse(stats, error_msg_false)


def subscriber_exists(self, subscriber_email, boolean, extra_text=''):
    try:
        first_text = f"For view '{self.view_name}', a"
    except AttributeError:
        first_text = 'A'
    error_msg_true = f"{first_text} subscriber with email address '{subscriber_email}' does not exist{extra_text}"
    error_msg_false = f"{first_text} subscriber with email address '{subscriber_email}' should not exist{extra_text}"
    try:
        subscriber = Subscriber.objects.get(
            subscriber_email=subscriber_email,
        )
    except ObjectDoesNotExist:
        subscriber = Subscriber.objects.none()
    if boolean:
        self.assertTrue(subscriber, error_msg_true)
    else:
        self.assertFalse(subscriber, error_msg_false)


def check_subscriber_count(self, count):
    subscriber_count = Subscriber.objects.count()
    error_msg = f"For view '{self.view_name}', the number of subscribers was '{str(subscriber_count)}', not '{str(count)}'"
    self.assertEqual(subscriber_count, count, error_msg)


def check_subscription_count(self, count):
    subscription_count = self.subscriber.subscriptions.count()
    error_msg = f"For view '{self.view_name}', subscriber '{self.subscriber.subscriber_email}', the number of subscriptions was '{str(subscription_count)}', not '{str(count)}'"
    self.assertEqual(subscription_count, count, error_msg)


def check_attached_trackers(self, count_dict=None, set_dict=None):
    if count_dict is None:
        count_dict = {}
    if set_dict is None:
        set_dict = {}
    for key, value in count_dict.items():
        tracker_count = getattr(self.test_instance, key).count()
        error_msg = f"For command '{self.test_command}', the number of trackers assigned to '{key}' was '{str(tracker_count)}', not '{str(value)}'"
        self.assertEqual(tracker_count, value, error_msg)
    for key, value in set_dict.items():
        tracker_list = list(getattr(self.test_instance, key).all())
        value_list = list(value)
        error_msg = f"For command '{self.test_command}', the list of trackers assigned to '{key}' was '{str(tracker_list)}', not '{str(value_list)}'"
        self.assertEqual(tracker_list, value_list, error_msg)


def check_site_profile_count(self, count):
    site_profile_count = SiteProfile.objects.count()
    error_msg = f"The number of site profiles was '{str(site_profile_count)}', not '{str(count)}'"
    self.assertEqual(site_profile_count, count, error_msg)


def check_site_profile(self, test_site, test_dict):
    error_msg_exists = f"A site profile matching the site with domain '{test_dict['domain']}' does not exist"
    try:
        site_profile = SiteProfile.objects.get(
            site_ptr=test_site,
        )
        profile_created = True
        for key, value in test_dict.items():
            attr_value = getattr(site_profile, key)
            error_msg_attr = f"A site profile that should have had the value '{test_dict[key]}' for attribute '{key}' instead had '{attr_value}'"
            self.assertEqual(value, attr_value, error_msg_attr)
        error_msg_protocol = f"The site profile with domain '{site_profile.domain}' had the protocol '{site_profile.protocol}' and not 'https://'"
        self.assertEqual(site_profile.protocol, 'https://', error_msg_protocol)
    except ObjectDoesNotExist:
        profile_created = False
    self.assertTrue(profile_created, error_msg_exists)


def check_subscriber_attributes(self, subscriber_email, attributes, boolean, extra_text=''):
    checked_subscriber = Subscriber.objects.get(
        subscriber_email=subscriber_email,
    )
    subscription_pks = checked_subscriber.subscriptions.values_list('pk', flat=True)
    subscription_list = []
    for pk in subscription_pks:
        subscription_list.append(str(pk))
    subscriber_data = {
        'first_name': checked_subscriber.first_name,
        'last_name': checked_subscriber.last_name,
        'subscriber_email': checked_subscriber.subscriber_email,
        'subscription_choices': subscription_list,
        'mc_email': checked_subscriber.mc_email,
    },
    for key in attributes.keys():
        error_msg_true = f"For view '{self.view_name}', subscriber '{subscriber_email}', the value of '{key}' was '{subscriber_data[0][key]}', not '{attributes[key]}'{extra_text}"
        error_msg_false = f"For view '{self.view_name}', subscriber '{subscriber_email}', the value of '{key}' should not be '{attributes[key]}'{extra_text}"
        if boolean:
            self.assertEqual(attributes[key], subscriber_data[0][key], error_msg_true)
        else:
            self.assertNotEqual(attributes[key], subscriber_data[0][key], error_msg_false)


def check_quantity_email_sent(self, quantity, clear_outbox=False, extra_text=''):
    try:
        first_text = f"For view '{self.view_name}', t"
    except AttributeError:
        first_text = 'T'
    emails_sent = len(mail.outbox)
    error_msg = f"{first_text}he number of emails sent was '{str(emails_sent)}', not '{str(quantity)}'{extra_text}"
    self.assertEqual(emails_sent, quantity, error_msg)
    if clear_outbox:
        mail.outbox = []


def check_quantity_trackers(self, quantity):
    tracker_count = EmailTracker.objects.count()
    error_msg = f"For command '{self.test_command}', the number of trackers existing was '{str(tracker_count)}', not '{str(quantity)}'"
    self.assertEqual(tracker_count, quantity, error_msg)


def check_email(self, email_number=0, subject=None, text_strings=None, html_strings=None):
    checked_email = mail.outbox[email_number]
    email_subject = checked_email.subject
    try:
        inserted_text = f"view '{self.view_name}'"
    except AttributeError:
        inserted_text = f"command '{self.test_command}'"
    error_msg_one = f"For {inserted_text}, email number '{str(email_number)}' did not have HTML alternative attached"
    error_msg_two = f"For {inserted_text}, email number '{str(email_number)}', HTML attachment did not have the MIME type 'text/html'"
    error_msg_three = f"For {inserted_text}, email number '{str(email_number)}' had the subject '{email_subject}', not '{subject}'"
    self.assertEqual(len(checked_email.alternatives), 1, error_msg_one)
    self.assertEqual(checked_email.alternatives[0][1], 'text/html', error_msg_two)
    if subject:
        self.assertEqual(email_subject, subject, error_msg_three)
    email_contains(
        self,
        checked_email,
        email_number,
        inserted_text,
        text_strings,
        html_strings,
    )


def status_code_equals(self, status_code):
    returned_code = self.response.status_code
    error_msg = f"For view '{self.view_name}', the status code returned was '{str(returned_code)}', not '{str(status_code)}'"
    self.assertEqual(returned_code, status_code, error_msg)


def redirect_url_equals(self, redirect_url):
    returned_url = self.response.url
    error_msg = f"For view '{self.view_name}', the redirect URL returned was '{returned_url}', not '{redirect_url}'"
    self.assertEqual(returned_url, redirect_url, error_msg)


def session_contains(self, value, boolean):
    error_msg_true = f"For view '{self.view_name}', the session did not contain '{value}'"
    error_msg_false = f"For view '{self.view_name}', the session should not contain '{value}'"
    if boolean:
        self.assertTrue(value in self.request.session, error_msg_true)
    else:
        self.assertFalse(value in self.request.session, error_msg_false)


def email_contains(self, checked_email, email_number, inserted_text, text_strings=None, html_strings=None):
    if text_strings is None:
        text_strings = []
    if html_strings is None:
        html_strings = []
    for string in text_strings:
        error_msg = f"For {inserted_text}, email number '{str(email_number)}' did not include '{string}' in its text body"
        self.assertIn(string, checked_email.body, error_msg)
    for string in html_strings:
        error_msg_one = f"For {inserted_text}, email number '{str(email_number)}' should not include '{string}' in its text body"
        error_msg_two = f"For {inserted_text}, email number '{str(email_number)}' did not include '{string}' in its HTML body"
        self.assertNotIn(string, checked_email.body, error_msg_one)
        self.assertIn(string, checked_email.alternatives[0][0], error_msg_two)


def html_contains(self, test_string, true_strings=None, false_strings=None):
    if true_strings is None:
        true_strings = []
    if false_strings is None:
        false_strings = []
    try:
        inserted_text = f"view '{self.view_name}'"
    except AttributeError:
        inserted_text = f"command '{self.test_command}'"
    for string in true_strings:
        error_msg = f"For {inserted_text}, the HTML did not contain '{string}'"
        self.assertTrue(string in test_string, error_msg)
    for string in false_strings:
        error_msg = f"For {inserted_text}, the HTML should not contain '{string}'"
        self.assertFalse(string in test_string, error_msg)


def json_contains(self, json_data=None, true_dict=None, false_dict=None):
    if true_dict is None:
        true_dict = {}
    if false_dict is None:
        false_dict = {}
    if json_data is None:
        self.tracker.refresh_from_db()
        data = self.tracker.json_data
    else:
        data = json_data
    for key, value in true_dict.items():
        error_msg_key = f"For view '{self.view_name}', the JSON data did not contain the key '{str(key)}'"
        error_msg_value = f"For view '{self.view_name}', the JSON data value for key '{str(key)}' was '{str(data[key])}' and not '{str(value)}'"
        self.assertIn(key, data.keys(), error_msg_key)
        self.assertEqual(value, data[key], error_msg_value)

    for key, value in false_dict.items():
        error_msg_key = f"For view '{self.view_name}', the JSON data should not contain the key '{str(key)}'"
        error_msg_value = f"For view '{self.view_name}', the JSON data value for key '{str(key)}' should not be '{str(value)}'"
        self.assertNotIn(key, data.keys(), error_msg_key)
        self.assertFalse(value, data[key], error_msg_value)


def image_contains(self, image_dict=None):
    if image_dict is None:
        image_dict = {}
    image_data = BytesIO(self.response.content)
    image_file = Image.open(image_data)
    for key, value in image_dict.items():
        error_msg = f"For view '{self.view_name}', the returned image's property '{key}' was not '{str(value)}'"
        image_property = getattr(image_file, key)
        self.assertIs(image_property, value, error_msg)


def check_http_response(self, form_load=False, status_code=200, redirect_url=None, true_strings=None, false_strings=None, true_dict=None, false_dict=None, image_dict=None):
    status_code_equals(
        self,
        status_code,
    )
    if redirect_url:
        redirect_url_equals(
            self,
            redirect_url,
        )
    session_contains(
        self,
        'form_load_time',
        form_load,
    )
    if true_strings or false_strings:
        html_contains(
            self,
            self.response.content.decode(),
            true_strings=true_strings,
            false_strings=false_strings,
        )
    if true_dict or false_dict:
        json_contains(
            self,
            true_dict=true_dict,
            false_dict=false_dict,
        )
    if image_dict:
        image_contains(
            self,
            image_dict,
        )


def check_permission(self, boolean):
    try:
        create_request_response(
            self,
            'get',
        )
        permission = True
    except PermissionDenied:
        permission = False
    error_msg_true = f"For view '{self.view_name}', access permission was denied"
    error_msg_false = f"For view '{self.view_name}', access permission was given"
    if boolean:
        self.assertTrue(permission, error_msg_true)
    else:
        self.assertFalse(permission, error_msg_false)


def check_not_found(self, boolean):
    try:
        create_request_response(
            self,
            'get',
        )
        not_found = False
    except Http404:
        not_found = True
    error_msg_true = f"For view '{self.view_name}', a 404 error was not returned"
    error_msg_false = f"For view '{self.view_name}', a 404 error was returned"
    if boolean:
        self.assertTrue(not_found, error_msg_true)
    else:
        self.assertFalse(not_found, error_msg_false)


def check_subscriber_subscription_state(self, subscriber_email, attributes, state, extra_text=''):
    """ """
    '''
    States
    0: Does not exist
    1: Exists with no subscriptions
    2: Exists with subscription one
    3: Exists with subscription two
    4: Exists with subscriptions one and two
    '''
    if state == 0:
        subscriber_exists(
            self,
            subscriber_email,
            False,
            extra_text=extra_text,
        )
    else:
        subscriber_exists(
            self,
            subscriber_email,
            True,
            extra_text=extra_text,
        )
        subscription_one = str(self.subscription_one.pk)
        subscription_two = str(self.subscription_two.pk)
        subscription_choices = []
        if state == 2 or state == 4:
            subscription_choices += [
                subscription_one,
            ]
        if state == 3 or state == 4:
            subscription_choices += [
                subscription_two,
            ]
        attributes['subscription_choices'] = subscription_choices
        check_subscriber_attributes(
            self,
            subscriber_email,
            attributes,
            True,
            extra_text=extra_text,
        )


def check_form_is_valid(self, boolean, extra_text=''):
    self.form = self.form_class(
        data=self.data,
    )
    error_msg_true = f'The form is not valid but should be{extra_text}'
    error_msg_false = f'The form is valid but should not be{extra_text}'
    if boolean:
        self.assertTrue(self.form.is_valid(), error_msg_true)
    else:
        self.assertFalse(self.form.is_valid(), error_msg_false)


def check_field_in_form(self, key, boolean):
    self.form = self.form_class(
        data=self.data,
    )
    self.form.save(commit=False)
    if key in self.form.cleaned_data.keys():
        key_present = True
    else:
        key_present = False
    error_msg_true = f"The key '{key}' was not present in the form's cleaned data and should have been"
    error_msg_false = f"The key '{key}' was present in the form's cleaned data and should not have been"
    if boolean:
        self.assertTrue(key_present, error_msg_true)
    else:
        self.assertFalse(key_present, error_msg_false)


def compare_secret_keys(self, secret_key_old, secret_key_new):
    error_msg = 'The secret key was not changed'
    self.assertNotEqual(secret_key_old, secret_key_new, error_msg)
