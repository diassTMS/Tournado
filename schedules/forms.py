from django import forms
from tournaments.models import Tournament
from leagues.models import League
from django.forms.widgets import HiddenInput
import math
from .models import Timings, Schedule, Rules, PitchNames

class ScheduleForm(forms.ModelForm): 
    class Meta:
        model = Tournament
        fields = ['noTeams', 'noDivisions', 'noPitches', 'knockoutRounds', 'liveScores', 'umpires', 'startTime', 'endTime', 'matchType']

        widgets = {
            'startTime': forms.TimeInput(attrs={'type': 'time'}),
            'endTime': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super(ScheduleForm, self).__init__(*args, **kwargs)
        self.fields['noTeams'].disabled = True
        self.fields['noDivisions'].disabled = True

        self.fields['noPitches'].label = f'No. Pitches'
        self.fields['noDivisions'].label = f'No. Divisions'
        self.fields['knockoutRounds'].label = f'Select knockout round option:'
        self.fields['liveScores'].label = f'Enable real time match scoring?'
        self.fields['umpires'].label = f'Independent umpire schedule?'
        self.fields['noTeams'].label = f'No. Entries'
        self.fields['startTime'].label = f'Start Time'
        self.fields['endTime'].label = f'Finish Time'
        self.fields['matchType'].label = f'Match Structure'            

    def clean_noTeams(self):
        cleaned_data = self.clean()
        teams = cleaned_data.get('noTeams')
        if teams < 3:
            self.add_error('noTeams', "Must have at least three entries.")
        return teams
    
    def clean_knockoutRounds(self):
        cleaned_data = self.clean()
        divs = cleaned_data.get('noDivisions')
        pitches = cleaned_data.get('noPitches')
        teams = cleaned_data.get('noTeams')
        knockouts = cleaned_data.get('knockoutRounds')

        if (divs == 3) and (knockouts != "None"):
            self.add_error('knockoutRounds', "You cannot have this option with three divisions.")
        if (divs == 4) and (pitches < 2):
            self.add_error('knockoutRounds', "You must have at least two pitches for this option.")
        if (divs == 4) and (knockouts == "Final"):
            self.add_error('knockoutRounds', "You cannot have this option with four divisions.")
        if (teams > 10) and (divs == 2) and (knockouts == 'Playoffs, Semis & Final'):
            self.add_error('knockoutRounds', "Unavailable for this number of teams")
        if (teams < 4) and (knockouts == 'Semis & Final'):
            self.add_error('knockoutRounds', "Must have four or more teams")
        return knockouts

    def clean_noPitches(self):
        cleaned_data = self.clean()
        pitches = cleaned_data.get('noPitches')
        if pitches > 8:
            self.add_error('noPitches', "Max number of pitches is 8")
        elif pitches < 1:
            self.add_error('noPitches', "Must have at least one pitch.")
        return pitches
    
    def clean_noDivisions(self):
        cleaned_data = self.clean()
        divs = cleaned_data.get('noDivisions')
        teams = cleaned_data.get('noTeams')

        if divs < 1:
            self.add_error('noDivisions', "Must have at least one division.")
        elif  math.floor(teams / divs) < 2:
            self.add_error('noDivisions', "Must have at least two teams per division")
        return divs

class SchedulePDFForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['tournament', 'timed',]

    def __init__(self, *args, **kwargs):
        super(SchedulePDFForm, self).__init__(*args, **kwargs)
        self.fields['tournament'].disabled = True     

        timings = Timings.objects.filter(
            schedule=self.instance
        ).order_by('order')
        print(timings)
        rules = Rules.objects.filter(
            schedule=self.instance
        ).order_by('order')

        pitches = PitchNames.objects.filter(schedule=self.instance)

        for i in range(len(timings) + 1):
            field_name = 'timing_%s' % (i + 1,)
            self.fields[field_name] = forms.CharField(required=False)
            try:
                self.initial[field_name] = timings[i].timing
            except IndexError:
                self.initial[field_name] = ""
                self.fields[field_name] = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Enter new timing here'}), required=False)

        for i in range(len(rules) + 1):
            field_name = 'rule_%s' % (i + 1,)
            self.fields[field_name] = forms.CharField(required=False)
            try:
                self.initial[field_name] = rules[i].rule
            except IndexError:
                self.initial[field_name] = ""
                self.fields[field_name] = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Enter new rule here'}), required=False)

        for i in range(len(pitches)):
            field_name = 'pitch_%s' % (i + 1,)
            self.fields[field_name] = forms.CharField(required=False)
            try:
                self.initial[field_name] = pitches[i].name
            except IndexError:
                self.initial[field_name] = ""

    def clean(self):
        timings = []
        rules = []
        pitches = []
        i = 0
        field_name = 'timing_%s' % (i + 1,)

        for field_name in self.fields:
            if field_name.startswith("timing_"):
                if self.cleaned_data.get(field_name) != "":
                    timing = self.cleaned_data[field_name]
                    print(timing)
                    timings.append(timing)
        
        self.cleaned_data["timings"] = timings

        j = 0
        field_name = 'rule_%s' % (j + 1,)

        for field_name in self.fields:
            if field_name.startswith("rule_"):
                if self.cleaned_data.get(field_name) != "":
                    rule = self.cleaned_data[field_name]
                    rules.append(rule)
        
        self.cleaned_data["rules"] = rules

        k = 0
        field_name = 'pitch_%s' % (k + 1,)

        for field_name in self.fields:
            if field_name.startswith("pitch_"):
                if self.cleaned_data.get(field_name) != "":
                    pitch = self.cleaned_data[field_name]
                    pitches.append(pitch)
        
        self.cleaned_data["pitches"] = pitches

    def save(self):
        schedule = self.instance
        schedule.timed = self.cleaned_data["timed"]
        schedule.save()

        oldTimings = Timings.objects.filter(schedule=schedule)
        oldTimings.delete()

        oldRules = Rules.objects.filter(schedule=schedule)
        oldRules.delete()

        oldPitches = PitchNames.objects.filter(schedule=schedule)

        count = 0
        for pitch in oldPitches:
            pitch.name = self.cleaned_data["pitches"][count]
            pitch.save()
            count += 1

        count = 1
        for timing in self.cleaned_data["timings"]:
            Timings.objects.create(
                schedule=schedule,
                timing=timing,
                order=count,
            )
            count += 1

        count = 1
        for rule in self.cleaned_data["rules"]:
            Rules.objects.create(
                schedule=schedule,
                rule=rule,
                order=count,
            )
            count += 1

    def get_timing_fields(self):
        for field_name in self.fields:
            if field_name.startswith("timing_"):
                yield self[field_name]

    def get_rule_fields(self):
        for field_name in self.fields:
            if field_name.startswith("rule_"):
                yield self[field_name]

    def get_pitch_fields(self):
        for field_name in self.fields:
            if field_name.startswith("pitch_"):
                yield self[field_name]

class TimingsForm(forms.ModelForm): 
    class Meta:
        model = Tournament
        fields = ['startTime', 'matchType', 'matchDuration', 'breakDuration', 'halftimeDuration']

        widgets = {
            'startTime': forms.TimeInput(attrs={'type': 'time'}),
            'endTime': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super(TimingsForm, self).__init__(*args, **kwargs)

        self.fields['startTime'].label = f'Start Time'
        self.fields['matchType'].label = f'Match Structure'            
        self.fields['matchDuration'].label = f'Match Duration' 
        self.fields['breakDuration'].label = f'Break Duration' 
        self.fields['halftimeDuration'].label = f'Half-time Duration'            

#LEAGUES

class LeagueScheduleForm(forms.ModelForm): 
    class Meta:
        model = League
        fields = ['noTeams', 'matchType','matchDuration', 'halftimeDuration']

    def __init__(self, *args, **kwargs):
        super(LeagueScheduleForm, self).__init__(*args, **kwargs)
        self.fields['noTeams'].disabled = True
        self.fields['matchType'].disabled = True

        self.fields['noTeams'].label = f'No. Entries'
        self.fields['matchType'].label = f'Match Structure'
        self.fields['matchDuration'].label = f'Half Durations'
        self.fields['halftimeDuration'].label = f'Half-time Duration'

        if self.instance.matchType == "One Way":
            self.fields['halftimeDuration'].disabled = True
            self.fields['matchDuration'].label = f'Match Duration'
            
    def clean_noTeams(self):
        cleaned_data = self.clean()
        teams = cleaned_data.get('noTeams')
        if teams < 3:
            self.add_error('noTeams', "Must have at least three entries.")
        return teams
    
    def clean_matchDuration(self):
        cleaned_data = self.clean()
        mDuration = cleaned_data.get('matchDuration')
        if mDuration < 1:
            self.add_error('matchDuration', "Duration must be at least 1 minute.")
        return mDuration

