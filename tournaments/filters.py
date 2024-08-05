import django_filters
from django.forms import DateInput
from tournaments.models import Tournament, Entry

class TournUserFilter(django_filters.FilterSet):
    date = django_filters.DateFilter(widget=DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Tournament
        fields = ['age','gender','group', 'date', 'user']

class EntryUserFilter(django_filters.FilterSet):
    class Meta:
        model = Entry
        fields = ['tournament']

