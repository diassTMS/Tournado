# Generated by Django 5.0.7 on 2025-03-22 16:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0041_alter_tournament_notes'),
    ]

    operations = [
        migrations.AddField(
            model_name='entry',
            name='invoiced',
            field=models.BooleanField(default=False),
        ),
    ]
