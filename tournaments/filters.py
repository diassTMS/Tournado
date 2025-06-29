import django_filters
from django.forms import SelectDateWidget, DateInput
from tournaments.models import Tournament, Entry
import datetime

class TournUserFilter(django_filters.FilterSet):
    date = django_filters.DateFilter(widget=DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Tournament
        fields = ['age','gender','group', 'date', 'user']

class EntryUserFilter(django_filters.FilterSet):
    currentYear = datetime.datetime.today().year
    tournament__date = django_filters.DateFilter(widget=SelectDateWidget(
        empty_label=("Year", "Month", "Day"),
        years= range(2024, currentYear+5),
    ))

    class Meta:
        model = Entry
        fields = ['tournament__age','tournament__gender','tournament__level', 'tournament__date']

