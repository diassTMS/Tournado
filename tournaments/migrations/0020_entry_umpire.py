# Generated by Django 5.0.7 on 2024-07-27 14:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0019_match_umpireone_match_umpiretwo'),
    ]

    operations = [
        migrations.AddField(
            model_name='entry',
            name='umpire',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
