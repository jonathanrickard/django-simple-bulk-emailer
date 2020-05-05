from django import (
    forms,
)
from django.conf import (
    settings,
)
from django.contrib import (
    admin,
)
from django.db import (
    models,
)


from adminsortable2.admin import (
    SortableAdminMixin,
    SortableInlineAdminMixin,
)
from django_simple_file_handler.file_types import (
    CHECK_DOC,
    CHECK_WEB_IMAGE,
)
from django_simple_file_handler.validators import (
    CheckExtMIME,
)


from .models import (
    BulkEmail,
    EmailDocument,
    EmailImage,
    MonthlyStat,
    SiteProfile,
    Subscriber,
    Subscription,
)


class BaseAdmin(admin.ModelAdmin):
    actions = None
    readonly_fields = [
        'created',
        'updated',
    ]
    bottom_fieldsets = [
        (
            'Date and time information', {
                'fields': [
                    'created',
                    'updated',
                ],
                'classes': [
                    'collapse',
                ],
            }
        ),
    ]
    fieldsets = bottom_fieldsets
    list_per_page = 20


class SiteProfileAdmin(BaseAdmin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.top_fieldsets = [
            (
                None, {
                    'fields': [
                        'protocol',
                        'domain',
                        'name',
                    ]
                }
            ),
        ]
        self.fieldsets = self.top_fieldsets + self.bottom_fieldsets

    search_fields = [
        'protocol',
        'domain',
        'name',
    ]
    list_display = [
        'name',
        'domain',
    ]
    ordering = [
        'name',
    ]


admin.site.register(
    SiteProfile,
    SiteProfileAdmin,
)


class SubscriptionAdmin(SortableAdminMixin, BaseAdmin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.readonly_fields = [
            'subscriber_count',
        ] + self.readonly_fields
        self.top_fieldsets = [
            (
                None, {
                    'fields': [
                        'list_name',
                        'descriptive_text',
                        'publicly_visible',
                        'use_pages',
                        'subscriber_count',
                    ]
                }
            ),
            (
                'MailChimp sync', {
                    'fields': [
                        'mc_sync',
                        'mc_user',
                        'mc_api',
                        'mc_list',
                    ],
                    'classes': [
                        'collapse',
                    ]
                }
            ),
            (
                'Advanced settings', {
                    'fields': [
                        'email_directory',
                        'page_directory',
                        'associated_model',
                    ],
                    'classes': [
                        'collapse',
                    ]
                }
            ),
        ]
        self.fieldsets = self.top_fieldsets + self.bottom_fieldsets

    search_fields = [
        'list_name',
    ]
    list_display = [
        'list_name',
        'subscriber_count',
        'publicly_visible',
        'list_link',
    ]


admin.site.register(
    Subscription,
    SubscriptionAdmin,
)


class SubscriberAdminForm(forms.ModelForm):
    subscriptions = forms.ModelMultipleChoiceField(
        queryset=Subscription.objects.order_by(
            'list_name',
        ),
        label='Subscriptions',
        required=False,
        widget=admin.widgets.FilteredSelectMultiple(
            'subscriptions',
            False,
        )
    )

    class Meta:
        model = Subscriber
        exclude = [
            'subscriber_key',
            'mc_email',
            'mc_synced',
        ]


class SubscriberAdmin(BaseAdmin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.readonly_fields = [
            'subscription_lists',
        ] + self.readonly_fields
        self.top_fieldsets = [
            (
                None, {
                    'fields': [
                        'first_name',
                        'last_name',
                        'subscriber_email',
                        'subscriptions',
                    ]
                }
            ),
        ]
        self.fieldsets = self.top_fieldsets + self.bottom_fieldsets

    def get_form(self, request, obj=None, **kwargs):
        if obj and not self.has_change_permission(request, obj):
            return super().get_form(request, obj, **kwargs)
        return SubscriberAdminForm

    search_fields = [
        'first_name',
        'last_name',
        'subscriber_email',
    ]
    list_display = [
        'subscriber_email',
        'first_name',
        'last_name',
        'subscription_lists',
    ]
    ordering = [
        'subscriber_email',
    ]


admin.site.register(
    Subscriber,
    SubscriberAdmin,
)


def get_image_widths():
    try:
        width_choices = settings.EMAILER_IMAGE_WIDTHS
    except AttributeError:
        width_choices = [
            (1080, 'Large'),
            (200, 'Small'),
        ]
    return width_choices


class EmailImageInlineForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['saved_file'].validators.append(CheckExtMIME(allowed_attributes=CHECK_WEB_IMAGE))

    image_width = forms.ChoiceField(
        label='Image size',
        choices=get_image_widths(),
    )

    class Meta:
        exclude = []


class EmailImageInline(admin.StackedInline):
    form = EmailImageInlineForm
    model = EmailImage
    fieldsets = [
        (
            None, {
                'fields': [
                    'image_width',
                    'description',
                    'caption',
                    'saved_file',
                ]
            }
        ),
    ]
    formfield_overrides = {
        models.CharField: {
            'widget': forms.TextInput(
                attrs={
                    'size': '95',
                },
            ),
        },
        models.TextField: {
            'widget': forms.Textarea(
                attrs={
                    'rows': 3,
                    'cols': 95,
                },
            ),
        },
    }
    extra = 0
    max_num = 1


class EmailDocumentInlineForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['saved_file'].validators.append(CheckExtMIME(allowed_attributes=CHECK_DOC))

    class Meta:
        exclude = []


class EmailDocumentInline(SortableInlineAdminMixin, admin.TabularInline):
    form = EmailDocumentInlineForm
    model = EmailDocument
    fieldsets = [
        (
            None, {
                'fields': [
                    'title',
                    'extra_text',
                    'saved_file',
                    'sort_order',
                ]
            }
        ),
    ]
    formfield_overrides = {
        models.TextField: {
            'widget': forms.Textarea(
                attrs={
                    'rows': 1,
                },
            ),
        },
    }
    extra = 0


class BulkEmailAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subscription_list'].queryset = Subscription.objects.filter(
            associated_model__contains=self.instance.__module__,
        ).filter(
            associated_model__contains=self.instance.__class__.__name__,
        )
        self.fields['subscription_list'].empty_label = None

    class Meta:
        model = BulkEmail
        exclude = [
            'sendable',
            'sending',
            'sent',
            'send_history',
        ]
        widgets = {
            'publication_date': admin.widgets.AdminDateWidget,
            'deletion_date': admin.widgets.AdminDateWidget,
        }


class BulkEmailAdmin(BaseAdmin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.readonly_fields = [
            'subscription_name',
            'short_headline',
            'page_preview',
            'email_preview',
        ] + self.readonly_fields
        self.top_fieldsets = [
            (
                None, {
                    'fields': [
                        'subscription_list',
                        'headline',
                        'body_text',
                    ]
                }
            ),
        ]
        self.middle_fieldsets = [
             (
                 None, {
                     'fields': [
                         'published',
                         'is_updated',
                         'publication_date',
                         'deletion_date',
                     ]
                 }
             ),
        ]
        self.fieldsets = self.top_fieldsets + self.middle_fieldsets + self.bottom_fieldsets

    def get_form(self, request, obj=None, **kwargs):
        if obj and not self.has_change_permission(request, obj):
            return super().get_form(request, obj, **kwargs)
        return BulkEmailAdminForm

    formfield_overrides = {
        models.CharField: {
            'widget': forms.TextInput(
                attrs={
                    'size': '95',
                },
            ),
        },
    }
    inlines = [
        EmailImageInline,
        EmailDocumentInline,
    ]
    search_fields = [
        'headline',
        'body_text',
    ]
    list_display = [
        'short_headline',
        'email_preview',
        'sent',
        'page_preview',
        'published',
        'subscription_name',
        'publication_date',
        'deletion_date',
    ]
    ordering = [
        '-publication_date',
        '-created',
    ]


admin.site.register(
    BulkEmail,
    BulkEmailAdmin,
)


class MonthlyStatAdmin(BaseAdmin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.readonly_fields = [
            'month_and_year',
            'stat_table',
        ] + self.readonly_fields
        self.top_fieldsets = [
            (
                None, {
                    'fields': [
                        'month_and_year',
                        'stat_table',
                    ]
                }
            ),
        ]
        self.fieldsets = self.top_fieldsets + self.bottom_fieldsets

    list_display = [
        'month_and_year',
    ]
    ordering = [
        '-year_int',
        '-month_int',
    ]

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    class Media:
        css = {
            'all': ('admin/css/django_simple_bulk_emailer.css',)
        }


admin.site.register(
    MonthlyStat,
    MonthlyStatAdmin,
)
