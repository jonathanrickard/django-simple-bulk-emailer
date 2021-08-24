from django.db import migrations, models
import django_simple_bulk_emailer.models


class Migration(migrations.Migration):

    dependencies = [
        ('django_simple_bulk_emailer', '0002_auto_20210812_1535'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bulkemail',
            name='is_updated',
        ),
        migrations.AddField(
            model_name='bulkemail',
            name='secondary_headline',
            field=models.TextField(blank=True, verbose_name='secondary headline (optional)'),
        ),
        migrations.AddField(
            model_name='bulkemail',
            name='update_text',
            field=models.TextField(blank=True, verbose_name='updates (optional)'),
        ),
        migrations.AlterField(
            model_name='bulkemail',
            name='deletion_date',
            field=models.DateField(blank=True, default=django_simple_bulk_emailer.models.get_deletion_date, null=True, verbose_name='deletion date (optional)'),
        ),
    ]
