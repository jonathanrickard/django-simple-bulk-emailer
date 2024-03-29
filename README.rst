==========================
django-simple-bulk-emailer
==========================

The django-simple-bulk-emailer Django app creates and distributes customizable bulk emails suitable for news articles and similar uses.
Optionally, it can produce customizable drop-in website article pages along with index pages for each subscription type.
Article pages include social media Open Graph tags, with the ability to specify a default image for pages without an image assigned.
The app can produce an unlimited number of subscriptions (email distribution lists), with different email and page templates for each.
Customizable user subscription management pages and emails are built in.

Refer to the `Django email documentation <https://docs.djangoproject.com/en/2.2/topics/email/>`_ for information on configuring a website to send email.

-----------
Quick start
-----------

1. Run ``pip install django-simple-bulk-emailer``.

2. Add django-simple-bulk-emailer and its dependencies to your installed apps: ::

    INSTALLED_APPS = (
        ...
        'django.contrib.sites',

        'adminsortable2',
        'ckeditor',
        'django_simple_bulk_emailer',
        'django_simple_file_handler',
    )

3. Run ``python manage.py migrate``.

4. Include the django-simple-bulk-emailer URLconf in your website's ``urls.py`` like this: ::

    urlpatterns = [
        ...
        url(
            r'^article-pages-path/',
            include('django_simple_bulk_emailer.urls')
        ),
    ]

5. If you are already using the Django sites framework, run ``python manage.py import_sites``.
You will then need to go to BULK EMAIL > Site profiles in your admin site and check to be sure your details are correct.
All new site profiles will be assigned an ``https://`` protocol, so change this if necessary.

If you are not already using the Django sites framework, go to your admin site and, under BULK EMAIL > Site profiles, create a profile with your site's information.
The ``SITE_ID`` setting is needed for django-simple-bulk-emailer.
See the `Django sites framework documentation <https://docs.djangoproject.com/en/2.2/ref/contrib/sites/>`_ for more information.

6. If you do not have Django sessions enabled (they are enabled by default), they will need to be enabled.
See the `Django sessions documentation <https://docs.djangoproject.com/en/2.2/topics/http/sessions/>`_ for more information.

------
Basics
------

Subscriptions (email distribution lists) are created and managed via the admin site.
Monthly email opens can also be tracked in the admin site. See the section on management commands for more information.

For information on customizable settings for images and linked files used with emails and pages, see the `django-simple-file-handler documentation <https://github.com/jonathanrickard/django-simple-file-handler>`_.

-------------
Subscriptions
-------------

Subscriptions (email distribution lists) are configured in the admin site.
The order of subscriptions can be changed by drag-and-drop, and this same order will be used in the options for choosing a distribution list when creating a bulk email.

The change list for this section of the admin site includes links to public-facing article index pages for subscriptions that use them.
Index page URLs follow the format ``example.com/article-pages-path/subscription-name-in-slug-form/``.

**Primary fields**

These apply to all subscriptions.

* ``List name`` — What you want the list to be called in user-facing pages.
* ``Descriptive text`` — Optional text that will appear at the top of the subscription's article index page.
* ``Publicly visible`` — A checkbox that determines whether the subscription is made available in user subscription-management pages. You may want private lists for testing purposes, etc. This also must be checked for page views to work.
* ``Use page view`` — A checkbox that determines whether article and index website pages will be generated for emails in the list.

**MailChimp sync**

These fields are self-explanatory and only need to be configured if you want to sync subscribers to this subscription with a MailChimp audience's contacts.
More information on MailChimp syncing is available below.

**Advanced settings**

These fields only need to be configured if the subscription needs to use custom templates or a custom email model (for example, if you want to subclass the BulkEmail model multiple times and have separate subscriptions associated with each).
Proceed with caution, as page views and email sending will not work correctly if these are not configured properly.

* ``Email template directory`` — Defaults to 'django_simple_bulk_emailer/subscription/emails'. See the section on custom templates for more information.
* ``Page template directory`` — Defaults to 'django_simple_bulk_emailer/subscription/pages'. See the section on custom templates for more information.
* ``Associated model`` — Defaults to 'django_simple_bulk_emailer.models.BulkEmail'. If set, assigns a different email model for use with a subscription so views and admin site sections will continue to work. If the subscription is only being used to manage MailChimp subscribers through your website, set this to 'None.' This will keep it from appearing as an option for the app's email distribution.

-----------
Subscribers
-----------

Names and email addresses for subscribers, as well as their subscriptions, can be changed through the admin site in addition to the user-facing pages.

The user-facing subscription page is at ``example.com/article-pages-path/subscriptions/subscribe``.

-----------
Bulk emails
-----------

The change list for this section of the admin site includes links to preview the HTML version of each email, as well as its article page (if pages are being used).
Emails are sent from the email preview pages.

Links to user-facing article pages can be found on the subscription index pages. See the section on subscriptions for more information.
URLs for user-facing article pages follow the format ``example.com/article-pages-path/subscription-name-in-slug-form/2019/8/1/19/email-headline-in-slug-form.html``.
If you remove "page-preview/" from the URL of the page preview, you will have the URL of the public-facing page.
with the first three numbers representing the year, month and day of publication and the fourth representing the database object's ID.
URL patterns only use the ID to retrieve the article, so feel free to change the headline or publication date after publication without fear of creating broken links.

**Primary fields**

* ``Subscription list`` — Which distribution list the email should be sent to. This also determines which index page the article will appear on.
* ``Headline`` — The email/article's headline, which will also appear in the email's subject line.
* ``Body text`` — This is a django-ckeditor field that allows you to create the HTML body text for your email with a WYSIWYG editor. See the `django-ckeditor documentation <https://github.com/django-ckeditor/django-ckeditor>`_ for information on customizing the editor. A sample configuration is given below.
* ``Published`` — A checkbox determining whether the public article page is accessible and whether the article appears on the subscription's index page.
* ``Has been updated`` — A checkbox to signify that changes have been made to the email. Adds "Updated: " to the beginning of the email subject line.
* ``Publication date`` — Defaults to the date the email was created.
* ``Deletion date`` — An optional date the email/article should be deleted from the database. See the sections on optional settings and management commands for more information.

**Image**

These fields only need to be configured if the email should have an image associated with it.

* ``Image size`` — Select from preset options how large the image should be. See the section on optional settings for more information.
* ``Screen reader description`` — Alt text to be associated with the image.
* ``Image caption`` — An optional caption to be displayed with the image.
* ``Uploaded file`` — The image file to be imported for processing.

**Documents**

Optionally, documents can be linked from the email/article page. Once the email has been saved, the documents can be arranged by drag-and-drop. The email must be saved again to preserve the order.

* ``Title`` — The name of the file to be displayed as a link. This also will be used to create a new file name for the file once it is uploaded.
* ``Extra text`` — Optional text to be displayed next to the file name link.
* ``Uploaded file`` — The document file to be imported for processing.

----------------------------------
Integrating article page templates
----------------------------------

To integrate article pages into your website, add the following to your ``base.html`` template:

* ``{% block emailer_head %}{% endblock %}`` between the template's ``<head></head>`` tags.
* ``{% block content %}{% endblock %}`` between the template's ``<body></body>`` tags.
* ``{% block emailer_foot %}`` between the template's ``<body></body>`` tags and below ``{% block content %}``. This is used to load a JavaScript file for the pages' responsive design.

----------------
Custom templates
----------------

Copying templates from the app and modifying them is the easiest way to create custom templates.

The ``BulkEmail`` model is the basis of both bulk emails and article pages.
It includes the following fields that may be useful in creating your own templates or accessing instances with your own code:

* ``headline`` — ``CharField``, ``max_length`` of 255
* ``secondary_headline`` — ``TextField``
* ``update_text`` — ``TextField``
* ``body_text`` — ``RichTextField`` (django-ckeditor HTML)
* ``publication_date`` — ``DateField``
* ``deletion_date`` — ``DateField``
* ``published`` — ``BooleanField``

Useful ``BulkEmail`` model methods include:

* ``short_headline`` — Returns a string of 30 characters or fewer, ending in an ellipsis if necessary
* ``first_paragraph`` — Returns the first paragraph from the ``body_text`` field, minus HTML tags, as a string
* ``email_headline`` — returns the ``headline`` field, but is easily overridden if subclassing the model
* ``email_body`` — Returns the ``body_text`` field, after making any substitutions specified in the ``EMAILER_SUBSTITUTIONS`` setting, as a string
* ``email_image`` — Returns the ``EmailImage`` instance associated with the ``BulkEmail`` instance if one exists
* ``email_documents`` — Returns a set of all ``EmailDocument`` instances associated with the ``BulkEmail`` instance
* ``subscription_name`` — Returns the name of the subscription associated with the ``BulkEmail`` instance as a string
* ``subscription_url`` — Returns the URL for the index page for the subscription associated with the ``BulkEmail`` instance as a string
* ``page_url`` — Returns the URL of the article page associated with the ``BulkEmail`` instance as a string
* ``protocol_domain`` — Returns the domain of the website, along with its protocol, as a string
* ``static_domain`` — Returns the domain of the website, along with its protocol,  as a string, unless the site's ``STATIC_URL`` setting specifies a protocol and domain
* ``media_domain`` — Returns the domain of the website, along with its protocol,  as a string, unless the site's ``MEDIA_URL`` setting specifies a protocol and domain

Useful ``EmailImage`` fields include:

* ``description`` — ``CharField``, ``max_length`` of 255
* ``caption`` — ``TextField``
* ``image_width`` — ``PositiveIntegerField``
* ``processed_file`` — ``FileField``

Useful ``EmailImage`` methods include:

* ``image_url`` — Returns the relative URL of the image in the ``processed_file`` field as a string
* ``image_height`` — Returns an integer for the height of the image in the ``processed_file`` field
* ``image_width`` — Returns an integer for the width of the image in the ``processed_file`` field


Useful ``EmailDocument`` fields include:

* ``title`` — ``CharField``, ``max_length`` of 245
* ``extra_text`` — ``TextField``
* ``saved_file`` — ``FileField``
* ``sort_order`` — ``PositiveIntegerField``

Useful ``EmailDocument`` methods include:

* ``file_url`` — Returns the relative URL of the file in the ``saved_file`` field as a string

**Email templates**

Template names include ``email_template_html.html`` and ``email_template_text.txt``.

Custom HTML email templates must begin with the ``{% extends basic_template %}`` tag.
This allows the template to be loaded into both the email preview page and the basic template used for email sending.

The ``BulkEmail`` instance is accessible in the template as ``{{ email_instance }}``.
See the information on fields and methods above.

**Article page templates**

Template names include ``list_view.html`` and ``page_view.html``.

The ``BulkEmail`` instance is accessible in the page template as ``{{ email_instance }}``.
See the information on fields and methods above.

**Other templates**

For information on customizing other templates, see the section on optional settings.

-------------
Form security
-------------

If `django-recaptcha <https://github.com/praekelt/django-recaptcha>`_ is installed and configured, django-simple-bulk-emailer will use it with the subscription form.
See the section on optional settings for more information.

Built-in security includes use of a hidden "honeypot" field and monitoring of the form's time-to-submit.
If either of these measures is violated, the form will appear to submit, but no data will be processed.


---------
MailChimp
---------

MailChimp syncing is optional. if you wish to sync with MailChimp, first run ``pip install mailchimp3``.

Changes made through MailChimp are synced immediately through a webhook. See the configuration information below.
Changes made locally are synced to MailChimp when the ``sync_mailchimp`` management command is run.

Other MailChimp notes:

* If a user changes their email address through MailChimp to one that already exists locally, the two local subscribers will be merged.
* Deleting a subscriber locally unsubscribes the contact in MailChimp, since deleting the address there would not allow it to be subscribed again in the future.
* If an email address is banned from an audience list by MailChimp, the subscription will be removed from the subscriber locally.
* Once an email address is unsubscribed from a MailChimp audience list, further changes on either end will not be synced due to limitations of the MailChimp API. As a result, a new contact will be created in the MailChimp audience list if the subscriber's email address has been changed locally while unsubscribed and the user is then resubscribed.

**Configuring a Mailchimp webhook**

The URL to use with the webhook will follow the format ``https://www.example.com/article-pages-path/mc-sync/sync?key=secretkey`` where ``secretkey`` is the secret key listed in your subscription's MailChimp sync settings. Because MailChimp does not support other forms of authentication for webhooks, this key is used and changes after each request. MailChimp's webhook URL is then updated automatically.

Check the boxes for what to sync:

* Subscribes
* Unsubscribes
* Profile updates
* Cleaned address
* Email changed

Also check the boxes for circumstances to sync:

* By a subscriber
* By an account admin

**Important**: Do not check the box for "From API," or you will create a syncing loop between the two systems.

-----------------
Optional settings
-----------------

* ``EMAILER_EMAIL_TEMPLATES`` — A string representing the path to a directory of email templates used by all subscriptions. Defaults to 'django_simple_bulk_emailer/universal/emails'.
* ``EMAILER_PAGE_TEMPLATES`` — A string representing the path to a directory of page templates used by all subscriptions. Defaults to 'django_simple_bulk_emailer/universal/pages'.
* ``EMAILER_FROM_ADDRESS`` — String. If set, this is the "from" address to be used in emails. Defaults to the ``DEFAULT_FROM_EMAIL`` setting.
* ``EMAILER_REPLY_ADDRESS`` — String. If set, this is the "reply-to" address to be used in emails. Defaults to the "from" address.
* ``EMAILER_SUBSTITUTIONS`` — Dictionary. If set, determines which substitutions will be made in the HTML of the emails' body text. A sample dictionary is available below.
* ``EMAILER_EMAIL_DELETE_DAYS`` — Positive integer. If set, gives the deletion date field a default value this many days from the current date. Deletion date is only used if the management command is executed. Does not affect tracking of email opens.
* ``EMAILER_TRACKING_MONTHS`` — Positive integer. Number of months for emails to be tracked for monthly stats. Defaults to 3. The higher this number is set, the longer the ``update_email_stats`` management command will take to run. Once removed from tracking, emails cannot be reinstated.
* ``EMAILER_STATS_SAVED`` — Positive integer. Number of most-recent monthly stats to keep in the database if the ``delete_expired_stats`` management command is run. Defaults to 12.
* ``EMAILER_PAGINATION`` — Boolean. If set to False, will stop list views from being paginated. Defaults to True.
* ``EMAILER_PAGINATION_RESULTS`` — Positive integer. If set, determines the number of results per page in list view. Defaults to 10.
* ``EMAILER_IMAGE_WIDTHS`` — A list of tuples. If set, will change the image width choices in the admin. Images will be scaled proportionally. The default widths list is given as an example below.
* ``EMAILER_SUBSCRIBE_SUBJECT`` — A string used as the subject line for an email sent to someone entering an email address in the subscription page. Defaults to 'Manage your email subscriptions'.
* ``EMAILER_RECAPTCHA_TYPE`` — Integer. Selects which version of reCAPTCHA to use if django-recaptcha is installed and configured. Choices are 1 (v2 checkbox), 2 (v2 invisible) or 3 (v3). Defaults to 1.
* ``EMAILER_RECAPTCHA_ATTRS`` — Dictionary. Data attributes to be passed on to the reCAPTCHA field. See django-recaptcha documentation for more information.
* ``EMAILER_RECAPTCHA_PARAMS`` — Dictionary. API parameters to be passed on to the reCAPTCHA field. See django-recaptcha documentation for more information.
* ``EMAILER_DEFAULT_IMAGE`` — String. Full URL for a default image (such as a logo) to be used when sharing email pages to social media when no image is included in the email.
* ``EMAILER_DEFAULT_TYPE`` — String. Image type for default image, such as ``'image/png'``.
* ``EMAILER_DEFAULT_WIDTH`` — String. Width for default image.
* ``EMAILER_DEFAULT_HEIGHT`` — String. Height for default image.
* ``EMAILER_DEFAULT_ALT`` — String. Alt text for default image.

-------------------
Management commands
-------------------

It is recommended that these commands be run by cron jobs or another method on a regular schedule. It is also recommended that the text output be written to a log file.

* ``send_bulk_email`` — Goes through subscriptions in the order they are ranked in the admin and sends whichever bulk email was marked for sending first. This is to limit how long the function takes to execute and make it friendlier to "serverless" deployments such as AWS Lambda. Because it only sends one email, you may need to run this frequently.
* ``sync_mailchimp`` — If MailChimp is configured, syncs local subscriber changes to MailChimp.
* ``delete_unsubscribed_users`` — Optional command that removes subscribers who do not have any subscriptions and were created at least one day ago.
* ``delete_expired_emails`` — Optional command that deletes emails which have reached or passed their deletion date.
* ``delete_expired_stats`` — Optional command that deletes monthly stats which have reached or passed their deletion date.
* ``update_email_stats`` — Optional command that updates the monthly statistics for email opens. It is suggested that this be run daily.

------------
Advanced use
------------

The app uses modular, reusable mixins and functions that can, of course, be imported for use with your own code.

You may wish to create a custom bulk email app by subclassing elements of this app.
For instance, you may wish to override the ``email_subject``, ``email_headline`` and ``email_body`` methods on the ``BulkEmail`` model.
It is suggested you use proxy models to get any of this app's models you do not need to customize into your app.
Note that classes in the app's ``admin.py`` file makes use of ``top_fieldsets`` and ``bottom_fieldsets`` (along with ``middle_fieldsets`` in ``BulkEmailAdmin``) to allow you to subclass these and insert your own fields at various points in the admin change page.

---------------
Sample settings
---------------

**Sample substitution dictionary** ::

    EMAILER_SUBSTITUTIONS = {
        ' target="_blank"': '',
    }

**Default widths list** ::

    EMAILER_IMAGE_WIDTHS = [
        (1200, 'Banner'),
        (900, 'Large'),
        (600, 'Medium'),
        (300, 'Small'),
    ]

**Sample django-ckeditor configuration settings** ::

    CKEDITOR_CONFIGS = {
        'default': {
            'disableNativeSpellChecker': False,
            'resize_dir': 'both',
            'width': '100%',
            'toolbar': 'Custom',
            'toolbar_Custom': [
                ['Undo', 'Redo'],
                ['Find', 'Replace'],
                ['Source'],
                ['Maximize'],
                '/',
                ['Format', 'Bold', 'Italic', 'Underline', 'Strike'],
                ['RemoveFormat'],
                ['NumberedList','BulletedList', '-', 'Outdent', 'Indent'],
                ['JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
                ['Subscript', 'Superscript'],
                ['SpecialChar', 'PasteText',],
                ['Link', 'Unlink'],
            ],
            'allowedContent': True,
            'extraAllowedContent': 'iframe[*]',
        },
    }

    TEXT_ADDITIONAL_TAGS = [
        'iframe',
    ]

    TEXT_ADDITIONAL_ATTRIBUTES = [
        'scrolling',
        'allowfullscreen',
        'webkitallowfullscreen',
        'mozallowfullscreen',
        'frameborder',
        'src',
        'height',
        'width',
    ]

