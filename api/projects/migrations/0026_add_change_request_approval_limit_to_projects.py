# Generated by Django 4.2.15 on 2024-09-20 14:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0025_add_change_request_project_permissions"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="minimum_change_request_approvals",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
