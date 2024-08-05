import django_filters
from django.forms import DateInput
from tournaments.models import Tournament
from django.contrib.auth.models import User, Group

class TournFilter(django_filters.FilterSet):
    date = django_filters.DateFilter(widget=DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Tournament
        fields = ['age','gender','group', 'date']

class LeagueFilter(django_filters.FilterSet):
    startDate = django_filters.DateFilter(widget=DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Tournament
        fields = ['age','gender','group', 'startDate']

class UserFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(method='filterOne', label="Search")
    groups = django_filters.ModelChoiceFilter(queryset=Group.objects.all())

    class Meta:
        model = User
        fields = ['name','groups',]

    def filterOne(self, queryset, name, value):
        return queryset.filter(username__icontains=value)
    