# Generated by Django 5.0.7 on 2024-08-05 18:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0027_alter_entry_teamsheet'),
    ]

    operations = [
        migrations.AddField(
            model_name='tournament',
            name='teamsheets',
            field=models.BooleanField(default=True),
        ),
    ]
