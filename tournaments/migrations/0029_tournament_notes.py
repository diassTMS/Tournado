# Generated by Django 5.0.7 on 2024-09-22 13:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0028_tournament_teamsheets'),
    ]

    operations = [
        migrations.AddField(
            model_name='tournament',
            name='notes',
            field=models.TextField(blank=True),
        ),
    ]
