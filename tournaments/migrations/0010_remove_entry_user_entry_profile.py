# Generated by Django 5.0.7 on 2024-07-16 12:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0009_entry'),
        ('users', '0002_profile_team'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='entry',
            name='user',
        ),
        migrations.AddField(
            model_name='entry',
            name='profile',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='users.profile'),
            preserve_default=False,
        ),
    ]
