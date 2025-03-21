from django.db import models
from django.contrib.auth.models import User
from users.models import Profile
from decimal import Decimal
from django.conf import settings
CURRENCY = settings.CURRENCY
TOURN_PRICE = settings.TOURN_PRICE

class Tournament(models.Model):
    
    GENDER = [                  
        ('Girls',"Girls"),
        ('Boys',"Boys"),
        ('Mixed','Mixed'),
    ]
    
    LEVEL = [
        ('Tier 1','Tier 1'),
        ('Tier 2','Tier 2'),
        ('Tier 3','Tier 3'),
        ('County','County'),
        ('Regional','Regional'),
        ('National','National'),
        ('N/A','N/A'),
    ]

    GROUP = [
        ('School','School'),
        ('Club','Club'),
        ('Social','Social'),
        ('County','County'),    #Make distinction between county level and county group (Maybe change county group to GHA?)
        ('N/A','N/A'),
    ]

    AGE = [
        ('U8','Under 8s'),
        ('U9','Under 9s'),
        ('U10','Under 10s'),
        ('U11','Under 11s'),
        ('U12','Under 12s'),
        ('U13','Under 13s'),
        ('U14','Under 14s'),
        ('U15','Under 15s'),
        ('U16','Under 16s'),
        ('U17','Under 17s'),
        ('U18','Under 18s'),
        ('Mixed','Mixed ages'),
    ]

    KNOCKOUTS = [
        ('Final', 'Final'),
        ('Semis & Final', 'Semis & Final'),
        ('Playoffs, Semis & Final', 'Playoffs, Semis & Final'),
        ('None', 'None'),
    ]

    TIMINGS = [
        ('One Way', 'One Way'),
        ('Each Way', 'Each Way'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, null=True)
    age = models.CharField(max_length=5, choices=AGE)         #Defining attributes
    gender = models.CharField(max_length=5, choices=GENDER)
    date = models.DateField()
    venue = models.CharField(max_length=50)
    noPitches = models.IntegerField()
    noDivisions = models.IntegerField()
    noTeams = models.IntegerField(default=0)
    meetTime = models.TimeField()
    startTime = models.TimeField()
    matchType = models.CharField(max_length=10, choices=TIMINGS, default='One Way')
    matchDuration = models.IntegerField(default=15)
    halftimeDuration = models.IntegerField(default=0)
    breakDuration = models.IntegerField(default=5)
    knockoutRounds = models.CharField(max_length=25, choices=KNOCKOUTS, default='None')
    liveScores = models.BooleanField(default=False)
    generatedSchedule = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)
    umpires = models.BooleanField(default=False)
    teamsheets = models.BooleanField(default=True)
    entryPrice = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    vat = models.BooleanField(default=True)
    level = models.CharField(max_length=10, choices=LEVEL)
    group = models.CharField(max_length=7, choices=GROUP)
    notes = models.TextField(blank=True) #default

    def __str__(self):                    #Displaying tournament id as a concatenation of info
        return f'{self.name} {self.date}'
    
    def tag_price(self):
        return f'{CURRENCY}{self.entryPrice}'

class Entry(models.Model):    #Creating entry table/entity

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    umpire = models.CharField(max_length=100, blank=True, null=True)
    teamName = models.CharField(max_length=30)
    teamsheet = models.FileField(upload_to="team-sheets/", null=True, blank=True)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    division = models.IntegerField(default=0)
    rank = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    won = models.IntegerField(default=0)
    drawn = models.IntegerField(default=0)
    lost = models.IntegerField(default=0)
    forGoals = models.IntegerField(default=0)
    againstGoals = models.IntegerField(default=0)
    goalDiff = models.IntegerField(default=0)
    played = models.IntegerField(default=0)

    def __str__(self):                    #Displaying self id as a concatenation of info
        return str(self.teamName)

class Match(models.Model):    #Creating match table/entity

    TYPE = [
        ('Division','Division'),
        ('3rd/4th Playoff', '3rd/4th Playoff'),
        ('5th/6th Playoff', '5th/6th Playoff'),
        ('7th/8th Playoff', '7th/8th Playoff'),
        ('9th/10th Playoff', '9th/10th Playoff'),
        ('Quarter-Final','Quarter-Final'),
        ('Semi-Final','Semi-Final'),
        ('Final','Final'),
        ('Free','Free')
    ]

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    division = models.IntegerField(default=0)
    played = models.BooleanField(default=False)
    current = models.BooleanField(default=False)
    type = models.CharField(max_length=20, choices=TYPE, default='Division')
    entryOne = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name='One')    
    entryTwo = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name='Two')
    pitch = models.IntegerField(default=1)
    start = models.TimeField()
    end = models.TimeField()
    goalsOne = models.IntegerField(default=0)
    goalsTwo = models.IntegerField(default=0)
    pfOne = models.IntegerField(default=0)
    pfTwo = models.IntegerField(default=0)
    umpireOne = models.CharField(max_length=100, blank=True, null=True)
    umpireTwo = models.CharField(max_length=100, blank=True, null=True)
    umpireOneName = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name='UmpireOne', blank=True, null=True)
    umpireTwoName = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name='UmpireTwo', blank=True, null=True)

    def __str__(self):                    #Displaying self id as a concatenation of info
        return f'{self.entryOne} v. {self.entryTwo}'