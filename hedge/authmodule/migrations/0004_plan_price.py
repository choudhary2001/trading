# Generated by Django 5.1.1 on 2024-10-09 17:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authmodule', '0003_plan'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='price',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]