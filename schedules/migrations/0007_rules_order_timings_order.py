# Generated by Django 5.0.7 on 2024-07-21 16:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedules', '0006_remove_timings_end_remove_timings_start'),
    ]

    operations = [
        migrations.AddField(
            model_name='rules',
            name='order',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='timings',
            name='order',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]
