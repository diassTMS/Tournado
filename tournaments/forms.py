from .models import Tournament, Entry, Match
from django.forms.widgets import HiddenInput
from django.utils.safestring import mark_safe
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.db.models import Q
from django import forms
import datetime

class TournForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = ['name', 'age', 'gender', 'date', 'venue', 'noPitches', 'noDivisions', 'startTime', 'meetTime', 'matchType', 'knockoutRounds', 'liveScores', 'umpires', 'teamsheets','entryPrice', 'vat', 'level', 'group']

        widgets = {
            'date': forms.DateInput(attrs={'type':'date'}),
            'startTime': forms.TimeInput(attrs={'type': 'time'}),
            'meetTime': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super(TournForm, self).__init__(*args, **kwargs)
        self.fields['name'].label = f'Event Title'
        self.fields['noPitches'].label = f'No. Playable Pitches'
        self.fields['noDivisions'].label = f'No. Divisions'
        self.fields['knockoutRounds'].label = f'Select knockout round option:'
        self.fields['liveScores'].label = f'Enable real time match scoring?'
        self.fields['umpires'].label = f'Independent umpire schedule?'
        self.fields['startTime'].label = f'Start Time'
        self.fields['meetTime'].label = f'Meet Time'
        self.fields['matchType'].label = f'Match Structure'
        self.fields['entryPrice'].label = f'Entry Fee'
        self.fields['vat'].label = f'Incl. VAT'
        self.fields['teamsheets'].label = f'Collect Team Sheets?'


    def clean_date(self):
        cleaned_data = self.clean()
        date = cleaned_data.get('date')
        now = datetime.date.today()
        if date < now:
            self.add_error('date', "Date cannot be in the past")
        
        return date

    def clean_noPitches(self):
        cleaned_data = self.clean()
        pitches = cleaned_data.get('noPitches')

        if pitches > 4:
            self.add_error('noPitches', "Max number of pitches is 4")
        elif pitches < 0:
            self.add_error('noPitches', "Must have at least one pitch.")

        return pitches
    
    def clean_knockoutRounds(self):
        cleaned_data = self.clean()
        divs = cleaned_data.get('noDivisions')
        pitches = cleaned_data.get('noPitches')
        knockouts = cleaned_data.get('knockoutRounds')

        if (divs == 3) and (knockouts != "None"):
            self.add_error('knockoutRounds', "You cannot have this option with three divisions.")
        elif (divs == 4) and (pitches < 2):
            self.add_error('knockoutRounds', "You must have at least two pitches for this option.")
        elif (divs == 4) and (knockouts == "Final"):
            self.add_error('knockoutRounds', "You cannot have this option with four divisions.")
        return knockouts

    def clean_noDivisions(self):
        cleaned_data = self.clean()
        divisions = cleaned_data.get('noDivisions')

        if divisions <= 0:
            self.add_error('noDivisions', "Must have at least one division")
        elif divisions > 4:
            self.add_error('noDivisions', "Max number of divisions is 4")
        
        return divisions
    
class EntryForm(forms.ModelForm):
    price = forms.CharField()
    class Meta:
        model = Entry
        fields = ['tournament', 'price', 'teamName', 'umpire', 'user',]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        tourn = kwargs.pop('tourn')
        super(EntryForm, self).__init__(*args, **kwargs)

        self.fields['tournament'].queryset = Tournament.objects.all()
        self.fields['teamName'].label = f'Team Name'
        self.fields['tournament'].label = f'Event'

        if not(self.request.user.groups.filter(name="Admin").exists()):
            self.fields['user'].widget = forms.HiddenInput()
        
        self.fields['user'].initial = self.request.user
        self.fields['price'].disabled = True
        self.fields['price'].initial = mark_safe(f'£{ Tournament.objects.get(pk=tourn.id).entryPrice }')
        
        if tourn.id != 0:
            self.fields['tournament'].disabled = True
            self.fields['tournament'].initial = Tournament.objects.get(pk=tourn.id)

        if tourn.umpires == True:
            self.fields['umpire'].label = f'Team Umpire'
        else:
            self.fields['umpire'].widget = HiddenInput()
    
    def clean_teamName(self):
        cleaned_data = self.clean()
        tourn = cleaned_data.get('tournament')
        name = cleaned_data.get('teamName')
        
        try:
            Entry.objects.get(teamName=name, tournament=tourn)
        except Entry.DoesNotExist:
            pass
        else:
            self.add_error('teamName', 'Entry with this team name already exists! Please choose a different team name.')
        
        return name
    
    def clean_user(self):
        cleaned_data = self.clean()
        user = cleaned_data.get('user')
        tourn = cleaned_data.get('tournament')

        if not(user.groups.filter(name=tourn.group).exists() or user.groups.filter(name="Admin").exists()):
            self.add_error('user', "Invalid group! You cannot enter this event.")

        return user

class EntryUpdateForm(forms.ModelForm):
    class Meta:
        model = Entry
        fields = ['tournament', 'user', 'teamName', 'umpire', 'teamsheet', 'rank',]

    def __init__(self, *args, **kwargs):
        tourn = kwargs.pop('tourn')
        self.request = kwargs.pop('request')
        super(EntryUpdateForm, self).__init__(*args, **kwargs)

        self.fields['teamName'].label = f'Team Name'
        self.fields['tournament'].label = f'Event'

        if self.request.user.groups.filter(name="Admin").exists():
            self.fields['rank'].label = f'Seeding Rank'
        else:
            self.fields['user'].disabled = True
            self.fields['rank'].widget = HiddenInput()
        
        if tourn.id != 0:
            self.fields['tournament'].initial = tourn
            self.fields['tournament'].disabled = True
        else:
            self.fields['tournament'].queryset = Tournament.objects.filter(date__gt=datetime.date.today())

        if tourn.umpires == True:
            self.fields['umpire'].label = f'Team Umpire'
        else:
            self.fields['umpire'].widget = HiddenInput()

        if tourn.teamsheets == True:
            self.fields['teamsheet'].label = f'Team Sheet Upload'
        else:
            self.fields['teamsheet'].widget = HiddenInput()

    def clean_user(self):
        cleaned_data = self.clean()
        user = cleaned_data.get('user')
        tourn = cleaned_data.get('tournament')

        if not(user.groups.filter(name=tourn.group).exists() or user.groups.filter(name="Admin").exists()):
            self.add_error('user', "Invalid group! You cannot enter this event.")

        return user

class ResultForm(forms.ModelForm): 
    class Meta:
        model = Match
        fields = ['goalsOne','goalsTwo', 'pfOne', 'pfTwo', 'played']

    def __init__(self, *args, **kwargs):
        super(ResultForm, self).__init__(*args, **kwargs)
        if (self.instance.division != 0):
            self.fields['pfOne'].widget = HiddenInput()
            self.fields['pfTwo'].widget = HiddenInput()
        else:
            self.fields['pfOne'].label = f'Penalty flicks scored'
            self.fields['pfTwo'].label = f'Penalty flicks scored'
        
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

class MatchKnockoutUpdateForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['tournament', 'type', 'entryOne', 'entryTwo', 'pitch', 'start', 'end']

        widgets = {
            'start': forms.TimeInput(attrs={'type': 'time'}),
            'end': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super(MatchKnockoutUpdateForm, self).__init__(*args, **kwargs)

        self.fields['type'].label = f'Match Type'
        self.fields['tournament'].label = f'Event'
        self.fields['entryOne'].label = f'Team One'
        self.fields['entryTwo'].label = f'Team Two'

        self.fields['tournament'].disabled = True
        self.fields['type'].disabled = True
        self.fields['entryOne'].disabled = True
        self.fields['entryTwo'].disabled = True

class SignupForm(forms.Form):
    tournaments = forms.ModelChoiceField(widget=forms.CheckboxSelectMultiple, queryset=Tournament.objects.all())

    def __init__(self, *args, **kwargs):
        group = kwargs.pop('group')
        super(SignupForm, self).__init__(*args, **kwargs)
        self.fields['tournaments'].queryset = Tournament.objects.filter(group=group, date__gte=datetime.date.today())

        
