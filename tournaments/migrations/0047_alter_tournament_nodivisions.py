# Generated by Django 5.0.7 on 2025-07-14 12:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0046_alter_tournament_nodivisions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tournament',
            name='noDivisions',
            field=models.IntegerField(default=1),
        ),
    ]
