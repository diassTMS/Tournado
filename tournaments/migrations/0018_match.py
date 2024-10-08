# Generated by Django 5.0.7 on 2024-07-18 20:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0017_rename_usernew_entry_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='Match',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('division', models.IntegerField(default=0)),
                ('played', models.BooleanField(default=False)),
                ('current', models.BooleanField(default=False)),
                ('type', models.CharField(choices=[('Division', 'Division'), ('3rd/4th Playoff', '3rd/4th Playoff'), ('5th/6th Playoff', '5th/6th Playoff'), ('7th/8th Playoff', '7th/8th Playoff'), ('9th/10th Playoff', '9th/10th Playoff'), ('Quarter-Final', 'Quarter-Final'), ('Semi-Final', 'Semi-Final'), ('Final', 'Final')], default='Division', max_length=20)),
                ('pitch', models.IntegerField(default=1)),
                ('start', models.TimeField()),
                ('end', models.TimeField()),
                ('goalsOne', models.IntegerField(default=0)),
                ('goalsTwo', models.IntegerField(default=0)),
                ('pfOne', models.IntegerField(default=0)),
                ('pfTwo', models.IntegerField(default=0)),
                ('entryOne', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='One', to='tournaments.entry')),
                ('entryTwo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='Two', to='tournaments.entry')),
                ('tournament', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tournaments.tournament')),
            ],
        ),
    ]
