# Generated by Django 5.0.7 on 2024-07-20 16:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedules', '0001_initial'),
        ('tournaments', '0018_match'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schedule',
            name='tournament',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='tournaments.tournament'),
        ),
    ]
