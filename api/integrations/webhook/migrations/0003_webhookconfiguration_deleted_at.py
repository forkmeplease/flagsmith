# Generated by Django 3.2.18 on 2023-02-28 15:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webhook', '0002_add_uuid_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='webhookconfiguration',
            name='deleted_at',
            field=models.DateTimeField(blank=True, db_index=True, default=None, editable=False, null=True),
        ),
    ]
