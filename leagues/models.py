from django.db import models
from django.contrib.auth.models import User
from users.models import Profile

class League(models.Model):
    
    GENDER = [                  
        ('Female',"Female"),
        ('Male',"Male"),
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

    TIMINGS = [
        ('One Way', 'One Way'),
        ('Each Way', 'Each Way'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, null=True)
    age = models.CharField(max_length=5, choices=AGE)         #Defining attributes
    gender = models.CharField(max_length=10, choices=GENDER)
    startDate = models.DateField()
    endDate = models.DateField()
    noTeams = models.IntegerField(default=0)
    matchType = models.CharField(max_length=10, choices=TIMINGS, default='One Way')
    matchDuration = models.IntegerField(default=15)
    halftimeDuration = models.IntegerField(default=0)
    generatedSchedule = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)
    publish = models.BooleanField(default=False)
    level = models.CharField(max_length=10, choices=LEVEL)
    group = models.CharField(max_length=7, choices=GROUP)

    def __str__(self):                    #Displaying tournament id as a concatenation of info
        return f'{self.name} {self.startDate}-{self.endDate}'

class LeagueEntry(models.Model):    #Creating entry table/entity

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    teamName = models.CharField(max_length=30)
    league = models.ForeignKey(League, on_delete=models.CASCADE)
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

class LeagueMatch(models.Model):    #Creating match table/entity

    league = models.ForeignKey(League, on_delete=models.CASCADE)
    played = models.BooleanField(default=False)
    data = models.BooleanField(default=False)
    venue = models.CharField(max_length=100, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    entryOne = models.ForeignKey(LeagueEntry, on_delete=models.CASCADE, related_name='One')    
    entryTwo = models.ForeignKey(LeagueEntry, on_delete=models.CASCADE, related_name='Two')
    pitch = models.IntegerField(default=1)
    start = models.TimeField(blank=True, null=True)
    goalsOne = models.IntegerField(default=0)
    goalsTwo = models.IntegerField(default=0)

    def __str__(self):                    #Displaying self id as a concatenation of info
        return f'{self.entryOne} v. {self.entryTwo}'