from .models import League, LeagueEntry, LeagueMatch
from django.forms.widgets import HiddenInput
from django.utils import timezone
from django import forms
import datetime

class LeagueForm(forms.ModelForm):
    class Meta:
        model = League
        fields = ['name', 'age', 'gender', 'startDate', 'endDate', 'matchType', 'level', 'group']

        widgets = {
            'startDate': forms.DateInput(attrs={'type':'date'}),
            'endDate': forms.DateInput(attrs={'type':'date'}),
        }

    def __init__(self, *args, **kwargs):
        super(LeagueForm, self).__init__(*args, **kwargs)
        self.fields['name'].label = f'Event Title'
        self.fields['startDate'].label = f'Start Date'
        self.fields['endDate'].label = f'End Date'
        self.fields['matchType'].label = f'Match Structure'

class LeagueEntryForm(forms.ModelForm):
    class Meta:
        model = LeagueEntry
        fields = ['league', 'teamName', 'user']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        league = kwargs.pop('league')
        super(LeagueEntryForm, self).__init__(*args, **kwargs)

        self.fields['league'].queryset = League.objects.all()
        self.fields['teamName'].label = f'Team Name'
        self.fields['league'].label = f'League'

        if not(self.request.user.groups.filter(name="Admin").exists()):
            self.fields['user'].widget = forms.HiddenInput()
        
        self.fields['user'].initial = self.request.user
        
        if league != 0:
            self.fields['league'].disabled = True
            self.fields['league'].initial = League.objects.get(pk=league)
    
    def clean_teamName(self):
        cleaned_data = self.clean()
        league = cleaned_data.get('league')
        name = cleaned_data.get('teamName')
        
        try:
            LeagueEntry.objects.get(teamName=name, league=league)
        except LeagueEntry.DoesNotExist:
            pass
        else:
            self.add_error('teamName', 'Entry with this team name already exists! Please choose a different team name.')
        
        return name
    
    def clean_user(self):
        cleaned_data = self.clean()
        user = cleaned_data.get('user')
        league = cleaned_data.get('league')

        if not(user.groups.filter(name=league.group).exists() or user.groups.filter(name="Admin").exists()):
            self.add_error('user', "Invalid group! You cannot enter this event.")

        return user
    
class LeagueEntryUpdateForm(forms.ModelForm):
    class Meta:
        model = LeagueEntry
        fields = ['league', 'teamName', 'user']

    def __init__(self, *args, **kwargs):
        league = kwargs.pop('league')
        self.request = kwargs.pop('request')
        super(LeagueEntryUpdateForm, self).__init__(*args, **kwargs)

        self.fields['teamName'].label = f'Team Name'
        self.fields['league'].label = f'League'
        self.fields['league'].initial = League.objects.get(pk=league)


        if not(self.request.user.groups.filter(name="Admin").exists()):
            self.fields['user'].disabled = True
        
        if league != 0:
            self.fields['league'].disabled = True

    def clean_user(self):
        cleaned_data = self.clean()
        user = cleaned_data.get('user')
        league = cleaned_data.get('league')

        if not(user.groups.filter(name=league.group).exists() or user.groups.filter(name="Admin").exists()):
            self.add_error('user', "Invalid group! You cannot enter this event.")

        return user

class LeagueMatchUpdateForm(forms.ModelForm):
    class Meta:
        model = LeagueMatch
        fields = ['league', 'entryOne', 'entryTwo', 'pitch', 'venue', 'date', 'start', 'data']

        widgets = {
            'start': forms.TimeInput(attrs={'type': 'time'}),
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super(LeagueMatchUpdateForm, self).__init__(*args, **kwargs)

        self.fields['data'].widget = forms.HiddenInput()

        self.fields['league'].label = f'League'
        self.fields['entryOne'].label = f'Team One'
        self.fields['entryTwo'].label = f'Team Two'

        self.fields['league'].disabled = True
        self.fields['entryOne'].disabled = True
        self.fields['entryTwo'].disabled = True

class LeagueResultForm(forms.ModelForm): 
    class Meta:
        model = LeagueMatch
        fields = ['goalsOne','goalsTwo', 'played']

    def __init__(self, *args, **kwargs):
        super(LeagueResultForm, self).__init__(*args, **kwargs)
        self.fields['goalsOne'].label = f'Goals scored'
        self.fields['goalsTwo'].label = f'Goals scored'
        self.fields['played'].label = f'Finished?'

    def clean_goalsOne(self):
        cleaned_data = self.clean()
        goals = cleaned_data.get('goalsOne')
        if goals < 0:
            self.add_error('goalsOne', "The input is not valid")
        return goals

    def clean_goalsTwo(self):
        cleaned_data = self.clean()
        goals = cleaned_data.get('goalsTwo')
        if goals < 0:
            self.add_error('goalsTwo', "The input is not valid")
        return goals
    
class PublishForm(forms.ModelForm):
    class Meta:
        model = League
        fields = ['publish']
