from django import (
    forms,
)
from django.conf import (
    settings,
)


from .models import (
    Subscriber,
    Subscription,
)


def get_recaptcha_widget():
    from captcha.widgets import (
        ReCaptchaV2Checkbox,
        ReCaptchaV2Invisible,
        ReCaptchaV3,
    )
    captcha_attrs = {}
    captcha_params = {}
    try:
        captcha_attrs = settings.EMAILER_RECAPTCHA_ATTRS
    except AttributeError:
        pass
    try:
        captcha_params = settings.EMAILER_RECAPTCHA_PARAMS
    except AttributeError:
        pass
    widget_dict = {
        1: ReCaptchaV2Checkbox(attrs=captcha_attrs, api_params=captcha_params),
        2: ReCaptchaV2Invisible(attrs=captcha_attrs, api_params=captcha_params),
        3: ReCaptchaV3(attrs=captcha_attrs, api_params=captcha_params),
    }
    try:
        widget_type = settings.EMAILER_RECAPTCHA_TYPE
    except AttributeError:
        widget_type = 1
    return widget_dict[widget_type]


class GetSubscriberForm(forms.Form):
    """ """
    ''' Begin hidden field '''
    email = forms.EmailField(
        required=False,
    )
    ''' End hidden field '''
    subscriber_email = forms.EmailField(
    )
    if hasattr(settings, 'RECAPTCHA_PUBLIC_KEY') and hasattr(settings, 'RECAPTCHA_PRIVATE_KEY'):
        try:
            from captcha.fields import (
                ReCaptchaField,
            )
            captcha = ReCaptchaField(widget=get_recaptcha_widget())
        except ImportError:
            pass


class SubscriptionSelector(forms.ModelMultipleChoiceField):
    def __init__(self, *args, **kwargs):
        if 'queryset' not in kwargs:
            kwargs['queryset'] = Subscription.objects.filter(
                publicly_visible=True,
            )
        super().__init__(*args, **kwargs)


class ModifySubscriberForm(forms.ModelForm):
    subscription_choices = SubscriptionSelector(
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = Subscriber
        exclude = [
            'subscriptions',
            'subscriber_key',
            'mc_email',
            'mc_synced',
        ]
