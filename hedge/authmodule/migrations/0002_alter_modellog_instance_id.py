# Generated by Django 4.2.16 on 2024-10-01 19:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authmodule', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='modellog',
            name='instance_id',
            field=models.CharField(max_length=255),
        ),
    ]
