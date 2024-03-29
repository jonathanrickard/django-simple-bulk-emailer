import ckeditor.fields
import django.contrib.sites.models
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django_simple_bulk_emailer.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('sites', '0002_alter_domain_unique'),
        ('django_simple_file_handler', '0006_auto_20190429_1949'),
    ]

    operations = [
        migrations.CreateModel(
            name='BulkEmail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='last updated')),
                ('headline', models.CharField(max_length=254)),
                ('body_text', ckeditor.fields.RichTextField()),
                ('publication_date', models.DateField(default=django.utils.timezone.localdate)),
                ('deletion_date', models.DateField(blank=True, default=django_simple_bulk_emailer.models.get_deletion_date, null=True)),
                ('published', models.BooleanField(default=False)),
                ('is_updated', models.BooleanField(default=False, verbose_name='has been updated')),
                ('sendable', models.BooleanField(default=False)),
                ('sending', models.BooleanField(default=False)),
                ('sent', models.BooleanField(default=False)),
                ('send_history', models.TextField(blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EmailTracker',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='last updated')),
                ('subject', models.CharField(max_length=254)),
                ('subscription_name', models.CharField(max_length=254)),
                ('send_complete', models.DateTimeField(default=django.utils.timezone.now)),
                ('number_sent', models.PositiveIntegerField(default=0)),
                ('json_data', models.TextField(blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SiteProfile',
            fields=[
                ('site_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='sites.Site')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='last updated')),
                ('protocol', models.CharField(default='https://', max_length=254)),
            ],
            options={
                'abstract': False,
            },
            bases=('sites.site', models.Model),
            managers=[
                ('objects', django.contrib.sites.models.SiteManager()),
            ],
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='last updated')),
                ('list_name', models.CharField(max_length=254)),
                ('descriptive_text', ckeditor.fields.RichTextField(blank=True, verbose_name='descriptive text (if using page views)')),
                ('list_slug', models.CharField(blank=True, max_length=254)),
                ('publicly_visible', models.BooleanField(default=False)),
                ('use_pages', models.BooleanField(default=True, verbose_name='use page view')),
                ('email_directory', models.CharField(default='django_simple_bulk_emailer/subscription/emails', max_length=254, verbose_name='email template directory')),
                ('page_directory', models.CharField(default='django_simple_bulk_emailer/subscription/pages', max_length=254, verbose_name='page template directory')),
                ('associated_model', models.CharField(default='django_simple_bulk_emailer.models.BulkEmail', max_length=254)),
                ('mc_sync', models.BooleanField(default=False, verbose_name='MailChimp sync')),
                ('mc_user', models.CharField(default='username', max_length=254, verbose_name='MailChimp username')),
                ('mc_api', models.CharField(default='API_key', max_length=254, verbose_name='MailChimp API key')),
                ('mc_list', models.CharField(default='list_ID', max_length=254, verbose_name='MailChimp audience ID')),
                ('sort_order', models.PositiveIntegerField(default=0, verbose_name='order')),
            ],
            options={
                'ordering': ['sort_order'],
            },
        ),
        migrations.CreateModel(
            name='Subscriber',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='last updated')),
                ('subscriber_key', models.CharField(max_length=254)),
                ('first_name', models.CharField(default='Anonymous', max_length=254)),
                ('last_name', models.CharField(default='Subscriber', max_length=254)),
                ('subscriber_email', models.EmailField(max_length=254, unique=True, verbose_name='email address')),
                ('mc_email', models.EmailField(blank=True, max_length=254, verbose_name='MailChimp email address')),
                ('mc_synced', models.BooleanField(default=False)),
                ('subscriptions', models.ManyToManyField(blank=True, to='django_simple_bulk_emailer.Subscription')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MonthlyStat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='last updated')),
                ('year_int', models.PositiveIntegerField()),
                ('month_int', models.PositiveIntegerField()),
                ('stat_data', models.TextField(blank=True)),
                ('current_trackers', models.ManyToManyField(related_name='current', to='django_simple_bulk_emailer.EmailTracker')),
                ('older_trackers', models.ManyToManyField(related_name='older', to='django_simple_bulk_emailer.EmailTracker')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EmailImage',
            fields=[
                ('processedimage_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='django_simple_file_handler.ProcessedImage')),
                ('description', models.CharField(default='Image', max_length=254, verbose_name='screen reader description')),
                ('caption', models.TextField(blank=True, verbose_name='image caption (optional)')),
                ('image_width', models.PositiveIntegerField()),
                ('bulk_email', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='emailimage', to='django_simple_bulk_emailer.BulkEmail')),
            ],
            options={
                'verbose_name': 'image (optional)',
                'verbose_name_plural': 'image (optional)',
            },
            bases=('django_simple_file_handler.processedimage',),
        ),
        migrations.CreateModel(
            name='EmailDocument',
            fields=[
                ('temporarydocument_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='django_simple_file_handler.TemporaryDocument')),
                ('sort_order', models.PositiveIntegerField(default=0, verbose_name='order')),
                ('bulk_email', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='django_simple_bulk_emailer.BulkEmail')),
            ],
            options={
                'verbose_name': 'document',
                'ordering': ['sort_order'],
            },
            bases=('django_simple_file_handler.temporarydocument',),
        ),
        migrations.AddField(
            model_name='bulkemail',
            name='subscription_list',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='django_simple_bulk_emailer.Subscription'),
        ),
    ]
