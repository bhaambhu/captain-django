# Generated by Django 4.1.4 on 2022-12-23 11:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('knowledge', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='path',
            name='status',
        ),
        migrations.AddField(
            model_name='path',
            name='published',
            field=models.BooleanField(default=False),
        ),
    ]
