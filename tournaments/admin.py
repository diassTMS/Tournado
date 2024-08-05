from django.contrib import admin
from .models import Tournament, Entry, Match

admin.site.register(Tournament)
admin.site.register(Entry)
admin.site.register(Match)
