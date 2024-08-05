from django.contrib import admin
from .models import League, LeagueEntry, LeagueMatch

admin.site.register(League)
admin.site.register(LeagueEntry)
admin.site.register(LeagueMatch)