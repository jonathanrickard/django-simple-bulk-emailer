import calendar
from datetime import (
    timedelta,
)
from importlib import (
    import_module,
)


from django.conf import (
    settings,
)
from django.contrib.sites.models import (
    Site,
)
from django.db import (
    models,
)
from django.urls import (
    reverse,
)
from django.utils import (
    timezone,
)
from django.utils.crypto import (
    get_random_string,
)
from django.utils.formats import (
    localize,
)
from django.utils.html import (
    strip_tags,
)
from django.utils.safestring import (
    mark_safe,
)
from django.utils.text import (
    slugify,
)


from ckeditor.fields import (
    RichTextField,
)
from django_simple_file_handler.models import (
    ProcessedImage,
    TemporaryDocument,
)


class BaseMixin(models.Model):
    created = models.DateTimeField(
        auto_now_add=True,
    )
    updated = models.DateTimeField(
        'last updated',
        auto_now=True,
    )

    class Meta:
        abstract = True


class SiteProfile(BaseMixin, Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    protocol = models.CharField(
        max_length=255,
        default='https://',
    )

    def protocol_domain(self):
        return f'{self.protocol}{self.domain}'


def create_default_key():
    return get_random_string(20)


class Subscription(BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    list_name = models.CharField(
        max_length=255,
    )
    descriptive_text = RichTextField(
        'descriptive text (if using page views)',
        blank=True,
    )
    list_slug = models.CharField(
        max_length=255,
        blank=True,
    )
    publicly_visible = models.BooleanField(
        default=False,
    )
    use_pages = models.BooleanField(
        'use page view',
        default=True,
    )
    email_directory = models.CharField(
        'email template directory',
        max_length=255,
        default='django_simple_bulk_emailer/subscription/emails',
    )
    page_directory = models.CharField(
        'page template directory',
        max_length=255,
        default='django_simple_bulk_emailer/subscription/pages',
    )
    associated_model = models.CharField(
        max_length=255,
        default='django_simple_bulk_emailer.models.BulkEmail',
    )
    mc_sync = models.BooleanField(
        'MailChimp sync',
        default=False,
    )
    mc_user = models.CharField(
        'MailChimp username',
        max_length=255,
        default='username',
    )
    mc_api = models.CharField(
        'MailChimp API key',
        max_length=255,
        default='API_key',
    )
    mc_list = models.CharField(
        'MailChimp audience ID',
        max_length=255,
        default='list_ID',
    )
    secret_key = models.CharField(
        max_length=255,
        default=create_default_key,
    )
    sort_order = models.PositiveIntegerField(
        'order',
        default=0,
    )

    def __str__(self):
        return self.list_name

    def get_email_class(self):
        split_path = self.associated_model.rsplit('.', 1)
        module_path = split_path[0]
        class_name = split_path[-1]
        module = import_module(module_path)
        return getattr(module, class_name)

    def list_link(self):
        if self.publicly_visible and self.use_pages:
            page_url = reverse(
                'django_simple_bulk_emailer:list_view',
                kwargs={
                    'list_slug': self.list_slug,
                },
            )
            return mark_safe(
                f'<a href="{page_url}" target="_blank">Page</a>'
            )
        else:
            return ''
    list_link.short_description = 'List'

    def subscriber_count(self):
        subscriber_count = Subscriber.objects.filter(
            subscriptions=self,
        ).count()
        return f'{subscriber_count:,}'

    def save(self, *args, **kwargs):
        self.list_slug = slugify(self.list_name)
        if not self.secret_key:
            self.secret_key = get_random_string(20)
        super().save(*args, **kwargs)

    class Meta:
        ordering = [
            'sort_order',
        ]


class Subscriber(BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    subscriber_key = models.CharField(
        max_length=255,
    )
    first_name = models.CharField(
        max_length=255,
        default='Anonymous',
    )
    last_name = models.CharField(
        max_length=255,
        default='Subscriber',
    )
    subscriber_email = models.EmailField(
        'email address',
        unique=True,
    )
    subscriptions = models.ManyToManyField(
        Subscription,
        blank=True,
    )
    mc_email = models.EmailField(
        'MailChimp email address',
        blank=True,
    )
    mc_synced = models.BooleanField(
        default=False,
    )

    def __str__(self):
        return self.subscriber_email

    def subscription_lists(self):
        subscription_set = self.subscriptions.all().order_by(
            'list_name',
        )
        return ''.join(f'{subscription_item}, ' for subscription_item in subscription_set)[:-2]


def get_deletion_date():
    try:
        future_time = timezone.now() + timedelta(days=settings.EMAILER_EMAIL_DELETE_DAYS)
        return future_time.date()
    except AttributeError:
        return None


class BulkEmail(BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    subscription_list = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
    )
    headline = models.CharField(
        max_length=255,
    )
    body_text = RichTextField(
    )
    secondary_headline = models.TextField(
        'secondary headline (optional)',
        blank=True,
    )
    update_text = models.TextField(
        'updates (optional)',
        blank=True,
    )
    update_datetime = models.DateTimeField(
        blank=True,
        null=True,
    )
    publication_date = models.DateField(
        default=timezone.localdate,
    )
    deletion_date = models.DateField(
        'deletion date (optional)',
        default=get_deletion_date,
        blank=True,
        null=True,
    )
    published = models.BooleanField(
        default=False,
    )
    sendable = models.BooleanField(
        default=False,
    )
    sending = models.BooleanField(
        default=False,
    )
    sent = models.BooleanField(
        default=False,
    )
    send_history = models.TextField(
        blank=True,
    )

    def short_headline(self):
        if len(self.headline) > 30:
            headline = f'{self.headline[:27]}...'
        else:
            headline = self.headline
        return headline
    short_headline.short_description = 'headline'

    def __str__(self):
        return self.short_headline()

    def first_paragraph(self):
        return strip_tags(self.body_text.split('>', 1)[1].split('</p>', 1)[0])

    def email_subject(self):
        if self.update_text:
            return f'Updated: {self.headline}'
        else:
            return self.headline

    def email_headline(self):
        return self.headline

    def email_body(self):
        body_text = self.body_text
        try:
            for key, value in settings.EMAILER_SUBSTITUTIONS.items():
                body_text = body_text.replace(key, value)
        except AttributeError:
            pass
        return body_text

    def email_image(self):
        return self.emailimage.first()

    def email_documents(self):
        return self.documents.all()

    def subscription_name(self):
        try:
            list_name = self.subscription_list.list_name
        except AttributeError:
            list_name = 'None chosen'
        return list_name
    subscription_name.short_description = 'subscription list'

    def headline_slug(self):
        return slugify(self.headline)

    def subscription_url(self):
        try:
            url = reverse(
                'django_simple_bulk_emailer:list_view',
                kwargs={
                    'list_slug': self.subscription_list.list_slug,
                },
            )
        except AttributeError:
            url = ''
        return url

    def reverse_kwargs(self):
        return {
            'list_slug': self.subscription_list.list_slug,
            'year': self.publication_date.year,
            'month': self.publication_date.month,
            'day': self.publication_date.day,
            'pk': self.pk,
            'headline_slug': self.headline_slug(),
        }

    def page_url(self):
        try:
            url = reverse(
                'django_simple_bulk_emailer:page_view',
                kwargs=self.reverse_kwargs(),
            )
        except AttributeError:
            url = ''
        return url

    def page_preview(self):
        try:
            if self.subscription_list.use_pages and self.subscription_list.publicly_visible:
                preview_url = reverse(
                    'django_simple_bulk_emailer:page_preview',
                    kwargs=self.reverse_kwargs(),
                )
                link = mark_safe(
                    f'<a href="{preview_url}" target="_blank">Page</a>'
                )
            else:
                link = ''
        except AttributeError:
            link = ''
        return link
    page_preview.short_description = 'preview'

    def email_preview(self):
        try:
            preview_url = reverse(
                'django_simple_bulk_emailer:email_preview',
                kwargs={
                    'list_slug': self.subscription_list.list_slug,
                    'pk': self.pk,
                },
            )
            link = mark_safe(
                f'<a href="{preview_url}">Email</a>'
            )
        except AttributeError:
            link = ''
        return link
    email_preview.short_description = 'preview'

    def protocol_domain(self):
        site = Site.objects.get(
            id=settings.SITE_ID,
        )
        site_profile = SiteProfile.objects.filter(
            domain=site.domain,
        ).first()
        return site_profile.protocol_domain()

    def static_domain(self):
        if any(protocol in settings.STATIC_URL for protocol in ['http://', 'https://']):
            return ''
        else:
            return self.protocol_domain()

    def media_domain(self):
        if any(protocol in settings.MEDIA_URL for protocol in ['http://', 'https://']):
            return ''
        else:
            return self.protocol_domain()

    def save(self, *args, **kwargs):
        if self.pk:
            saved = BulkEmail.objects.get(pk=self.pk)
            if self.update_text != saved.update_text:
                self.update_datetime = timezone.now()
            else:
                self.update_datetime = saved.update_datetime
        super().save(*args, **kwargs)


class EmailImage(ProcessedImage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    bulk_email = models.ForeignKey(
        BulkEmail,
        on_delete=models.CASCADE,
        related_name='emailimage',
    )
    description = models.CharField(
        'screen reader description',
        max_length=255,
        default='Image',
    )
    caption = models.TextField(
        'image caption (optional)',
        blank=True,
    )
    image_width = models.PositiveIntegerField(
    )

    def __str__(self):
        return self.description

    def save(self, *args, **kwargs):
        self.output_width = self.image_width
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'image (optional)'
        verbose_name_plural = verbose_name


class EmailDocument(TemporaryDocument):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    bulk_email = models.ForeignKey(
        BulkEmail,
        on_delete=models.CASCADE,
        related_name='documents',
    )
    sort_order = models.PositiveIntegerField(
        'order',
        default=0,
    )

    class Meta:
        ordering = [
            'sort_order',
        ]
        verbose_name = 'document'


class EmailTracker(BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    subject = models.CharField(
        max_length=255,
    )
    subscription_name = models.CharField(
        max_length=255,
    )
    send_complete = models.DateTimeField(
        default=timezone.now,
    )
    number_sent = models.PositiveIntegerField(
        default=0,
    )
    json_data = models.JSONField(
        blank=True,
        null=True,
    )

    def send_complete_string(self):
        return localize(timezone.localtime(self.send_complete))


class MonthlyStat(BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    year_int = models.PositiveIntegerField(
    )
    month_int = models.PositiveIntegerField(
    )
    stat_data = models.TextField(
        blank=True,
    )
    current_trackers = models.ManyToManyField(
        EmailTracker,
        related_name='current',
    )
    older_trackers = models.ManyToManyField(
        EmailTracker,
        related_name='older',
    )

    def month_and_year(self):
        return f'{calendar.month_name[self.month_int]} {str(self.year_int)}'

    def __str__(self):
        return self.month_and_year()

    def stat_table(self):
        if self.stat_data:
            return mark_safe(
                f'<table id="emailer_table">{self.stat_data}</table>'
            )
        else:
            return ''
