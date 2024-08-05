import django_filters
from django.forms import DateInput
from .models import League, LeagueMatch
from django.db.models import Q

class LeagueUserFilter(django_filters.FilterSet):
    startDate = django_filters.DateFilter(widget=DateInput(attrs={'type': 'date'}))

    class Meta:
        model = League
        fields = ['age','gender','group', 'startDate', 'user']


class LeagueMatchFilter(django_filters.FilterSet):
    entry = django_filters.CharFilter(method='my_custom_filter', label="Search")

    class Meta:
        model = LeagueMatch
        fields = ['entry', 'played', 'venue', 'date', 'data']

    def my_custom_filter(self, queryset, name, value):
        return queryset.filter(
            Q(entryOne__teamName__icontains=value) |
            Q(entryTwo__teamName__icontains=value)
            )