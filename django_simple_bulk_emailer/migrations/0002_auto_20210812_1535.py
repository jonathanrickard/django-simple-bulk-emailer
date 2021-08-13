from django.db import migrations, models
import django_simple_bulk_emailer.models


class Migration(migrations.Migration):

    dependencies = [
        ('django_simple_bulk_emailer', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='secret_key',
            field=models.CharField(default=django_simple_bulk_emailer.models.create_default_key, max_length=255),
        ),
        migrations.AlterField(
            model_name='bulkemail',
            name='headline',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='bulkemail',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='emailimage',
            name='description',
            field=models.CharField(default='Image', max_length=255, verbose_name='screen reader description'),
        ),
        migrations.AlterField(
            model_name='emailtracker',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='emailtracker',
            name='json_data',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='emailtracker',
            name='subject',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='emailtracker',
            name='subscription_name',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='monthlystat',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='siteprofile',
            name='protocol',
            field=models.CharField(default='https://', max_length=255),
        ),
        migrations.AlterField(
            model_name='subscriber',
            name='first_name',
            field=models.CharField(default='Anonymous', max_length=255),
        ),
        migrations.AlterField(
            model_name='subscriber',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='subscriber',
            name='last_name',
            field=models.CharField(default='Subscriber', max_length=255),
        ),
        migrations.AlterField(
            model_name='subscriber',
            name='subscriber_key',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='associated_model',
            field=models.CharField(default='django_simple_bulk_emailer.models.BulkEmail', max_length=255),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='email_directory',
            field=models.CharField(default='django_simple_bulk_emailer/subscription/emails', max_length=255, verbose_name='email template directory'),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='list_name',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='list_slug',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='mc_api',
            field=models.CharField(default='API_key', max_length=255, verbose_name='MailChimp API key'),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='mc_list',
            field=models.CharField(default='list_ID', max_length=255, verbose_name='MailChimp audience ID'),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='mc_user',
            field=models.CharField(default='username', max_length=255, verbose_name='MailChimp username'),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='page_directory',
            field=models.CharField(default='django_simple_bulk_emailer/subscription/pages', max_length=255, verbose_name='page template directory'),
        ),
    ]
