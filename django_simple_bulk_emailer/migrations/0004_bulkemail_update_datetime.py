from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_simple_bulk_emailer', '0003_auto_20210824_1148'),
    ]

    operations = [
        migrations.AddField(
            model_name='bulkemail',
            name='update_datetime',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
