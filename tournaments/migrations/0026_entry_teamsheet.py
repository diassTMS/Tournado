# Generated by Django 5.0.7 on 2024-08-05 18:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0025_tournament_vat'),
    ]

    operations = [
        migrations.AddField(
            model_name='entry',
            name='teamsheet',
            field=models.FileField(blank=True, null=True, upload_to='media/team-sheets/'),
        ),
    ]
