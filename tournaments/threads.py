import numpy as np
import math
import random
import threading
from tournaments.models  import Entry, Match, Tournament
from django.contrib import messages
from ast import literal_eval
import datetime
from django.db.models import Q, F
from django.contrib.auth.models import User

class EntryUpdateThread(threading.Thread):
    def __init__(self, instance, prevMatch):
        self.instance = instance
        self.prevMatch = prevMatch
        threading.Thread.__init__(self)

    def run(self):
        try:

#--------------------------------------------------------------------------------------------------
#Sub Programs
#--------------------------------------------------------------------------------------------------

            def prevResults(entryOne, entryTwo, match):
                if match.goalsOne > match.goalsTwo:
                    entryOne.won -= 1
                    entryTwo.lost -= 1
                    entryOne.points -= 3

                elif match.goalsOne < match.goalsTwo:
                    entryOne.lost -= 1
                    entryTwo.won -=1
                    entryTwo.points -= 3  

                elif match.type != 'Division':
                    if match.pfOne > match.pfTwo:
                        entryOne.won -= 1
                        entryTwo.lost -= 1
                        entryOne.points -= 3

                    elif match.pfOne < match.pfTwo:
                        entryOne.lost -= 1
                        entryTwo.won -=1
                        entryTwo.points -= 3

                    entryOne.forGoals -= match.pfOne
                    entryTwo.forGoals -= match.pfTwo
                    entryOne.againstGoals -= match.pfTwo
                    entryTwo.againstGoals -= match.pfOne                                                                          
                
                else:
                    entryOne.drawn -= 1
                    entryTwo.drawn -= 1
                    entryOne.points -= 1
                    entryTwo.points -= 1

                entryOne.forGoals -= match.goalsOne
                entryTwo.forGoals -= match.goalsTwo
                entryOne.againstGoals -= match.goalsTwo
                entryTwo.againstGoals -= match.goalsOne
                entryOne.goalDiff = entryOne.forGoals - entryOne.againstGoals
                entryTwo.goalDiff = entryTwo.forGoals - entryTwo.againstGoals
                entryOne.played -= 1
                entryTwo.played -= 1

                entryOne.save()
                entryTwo.save()

                print('prev results updated')
            
            def validResults(entryOne, entryTwo, match):                
                if match.goalsOne > match.goalsTwo:
                    entryOne.won += 1
                    entryTwo.lost += 1
                    entryOne.points += 3

                elif match.goalsOne < match.goalsTwo:
                    entryTwo.won += 1
                    entryOne.lost += 1
                    entryTwo.points += 3

                elif match.type != 'Division':
                    if match.pfOne > match.pfTwo:
                        entryOne.won += 1
                        entryTwo.lost += 1
                        entryOne.points += 3

                    elif match.pfOne < match.pfTwo:
                        entryTwo.won += 1
                        entryOne.lost += 1
                        entryTwo.points += 3

                    entryOne.forGoals += match.pfOne
                    entryTwo.forGoals += match.pfTwo
                    entryOne.againstGoals += match.pfTwo
                    entryTwo.againstGoals += match.pfOne

                else:
                    entryOne.drawn += 1
                    entryTwo.drawn += 1
                    entryOne.points += 1
                    entryTwo.points += 1

                entryOne.played += 1
                entryTwo.played += 1

                entryOne.forGoals += match.goalsOne
                entryTwo.forGoals += match.goalsTwo
                entryOne.againstGoals += match.goalsTwo
                entryTwo.againstGoals += match.goalsOne
                entryOne.goalDiff = entryOne.forGoals - entryOne.againstGoals
                entryTwo.goalDiff = entryTwo.forGoals - entryTwo.againstGoals

                entryOne.save()
                entryTwo.save()

                print('entries Updated')

            def ranking(entryOne, entryTwo, match):
                if match.type == "Final":
                    rankOne = 1
                    rankTwo = 2
                elif match.type == "3rd/4th Playoff":
                    rankOne = 3
                    rankTwo = 4
                elif match.type =='5th/6th Playoff':
                    rankOne = 5
                    rankTwo = 6
                elif match.type == '7th/8th Playoff':
                    rankOne = 7
                    rankTwo = 8
                elif match.type == '9th/10th Playoff':
                    rankOne = 9
                    rankTwo = 10
                else:
                    rankOne = 0
                    rankTwo = 0

                if match.goalsOne > match.goalsTwo:
                    entryOne.rank = rankOne
                    entryTwo.rank = rankTwo

                elif match.goalsOne < match.goalsTwo:
                    entryOne.rank = rankTwo
                    entryTwo.rank = rankOne

                else:
                    if match.pfOne > match.pfTwo:
                        entryOne.rank = rankOne
                        entryTwo.rank = rankTwo

                    elif match.pfOne < match.pfTwo:
                        entryOne.rank = rankTwo
                        entryTwo.rank = rankOne

                entryOne.save()
                entryTwo.save()

                print('Ranks Updated')
            
            def playoffs(self, duration):
                print('Playoffs')
                noDivs = self.tournament.noDivisions
                if noDivs == 1:
                    print('One div')
                    entriesRanked = Entry.objects.filter(Q(tournament=self.tournament.id) & Q(division=1)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
                    
                    knockoutMatches = Match.objects.filter(Q(tournament=self.tournament.id) & Q(division=0))
                    if len(knockoutMatches) == 0:
                        types = ['Final',
                                '3rd/4th Playoff',
                                '5th/6th Playoff',
                                '7th/8th Playoff', 
                                '9th/10th Playoff',
                                ]
                        
                        for i in range(math.floor(len(entriesRanked) / 2)):
                            teamOne = entriesRanked[(2*i)]
                            teamTwo = entriesRanked[(2*i + 1)]

                            start = str(Match.objects.filter(tournament=self.tournament.id).last().end)
                            d = datetime.datetime.strptime(start, '%H:%M:%S')     
                            d += datetime.timedelta(minutes=self.tournament.breakDuration)
                            start = d
                            d += datetime.timedelta(minutes=duration)
                            end = d
                            
                            playoff = Match(tournament = self.tournament,
                                        type = types[i],                  
                                        entryOne = teamOne,
                                        entryTwo = teamTwo,
                                        pitch = 1,
                                        start = start,
                                        end = end,
                                        )
                            
                            playoff.save()

                if noDivs == 2:
                    print('Two div')
                    entriesRankedOne = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=1)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
                    entriesRankedTwo = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=2)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
                    
                    knockoutMatches = Match.objects.filter(Q(tournament=self.tournament.id) & Q(division=0))
                    final = Match.objects.filter(Q(tournament=self.tournament.id) & Q(type="Final"))
                    semis = Match.objects.filter(Q(tournament=self.tournament.id) & Q(type="Semi-Final") & Q(played=True))
                    if len(knockoutMatches) == 0:
                        #Semis
                        for i in range(2):
                            start = str(Match.objects.filter(tournament=self.tournament.id).last().end)
                            d = datetime.datetime.strptime(start, '%H:%M:%S')     
                            d += datetime.timedelta(minutes=self.tournament.breakDuration)
                            start = d
                            d += datetime.timedelta(minutes=duration)
                            end = d

                            if i == 0:
                                semi = Match(tournament = self.tournament,
                                            type = 'Semi-Final',                  
                                            entryOne = entriesRankedOne[0],
                                            entryTwo = entriesRankedTwo[1],
                                            pitch = 1,
                                            start = start,
                                            end = end,
                                            )
                            else:
                                semi = Match(tournament = self.tournament,
                                            type = 'Semi-Final',                  
                                            entryOne = entriesRankedOne[1],
                                            entryTwo = entriesRankedTwo[0],
                                            pitch = 1,
                                            start = start,
                                            end = end,
                                            )
                            semi.save()
                        
                        types = ['5th/6th Playoff',
                                '7th/8th Playoff', 
                                '9th/10th Playoff',
                                ]
                        
                        # Getting smaller division
                        if len(entriesRankedOne) <= len(entriesRankedTwo):
                            division = entriesRankedOne
                        else:
                            division = entriesRankedTwo

                        #Playoffs
                        for i in range(len(division)-2):
                            teamOne = entriesRankedOne[2 + i]
                            teamTwo = entriesRankedTwo[2 + i]

                            start = str(Match.objects.filter(tournament=self.tournament.id).last().end)
                            d = datetime.datetime.strptime(start, '%H:%M:%S')     
                            d += datetime.timedelta(minutes=self.tournament.breakDuration)
                            start = d
                            d += datetime.timedelta(minutes=duration)
                            end = d
                            
                            playoff = Match(tournament = self.tournament,
                                        type = types[i],                  
                                        entryOne = teamOne,
                                        entryTwo = teamTwo,
                                        pitch = 1,
                                        start = start,
                                        end = end,
                                        )
                            
                            playoff.save()

                    elif (len(final) == 0) and (len(semis) == 2):
                        print('Finals & 3rd/4th')
                        #Final & 3rd/4th Playoff
                        semis = Match.objects.filter(Q(tournament=self.tournament.id) & Q(type='Semi-Final'))
                        semiWinners = []
                        semiLosers = []

                        for match in semis:
                            if match.goalsOne > match.goalsTwo:
                                semiWin = match.entryOne
                                semiLoss = match.entryTwo

                            elif match.goalsOne < match.goalsTwo:
                                semiWin = match.entryTwo                                                            
                                semiLoss = match.entryOne

                            else:
                                if match.pfOne > match.pfTwo:
                                    semiWin = match.entryOne
                                    semiLoss = match.entryTwo
                                else:
                                    semiWin = match.entryTwo 
                                    semiLoss = match.entryOne  

                            semiWinners.append(semiWin)
                            semiLosers.append(semiLoss)      

                        start = str(Match.objects.filter(tournament=self.tournament.id).last().end)
                        d = datetime.datetime.strptime(start, '%H:%M:%S')     
                        d += datetime.timedelta(minutes=self.tournament.breakDuration)
                        start = d
                        d += datetime.timedelta(minutes=duration)
                        end = d    

                        playoff = Match(tournament = self.tournament,
                                        type = '3rd/4th Playoff',                  
                                        entryOne = semiLosers[0],
                                        entryTwo = semiLosers[1],
                                        pitch = 1,
                                        start = start,
                                        end = end,
                                        )   
                        playoff.save() 

                        start = str(Match.objects.filter(tournament=self.tournament.id).last().end)
                        d = datetime.datetime.strptime(start, '%H:%M:%S')     
                        d += datetime.timedelta(minutes=self.tournament.breakDuration)
                        start = d
                        d += datetime.timedelta(minutes=duration)
                        end = d                                      

                        final = Match(tournament = self.tournament,
                                        type = 'Final',                  
                                        entryOne = semiWinners[0],
                                        entryTwo = semiWinners[1],
                                        pitch = 1,
                                        start = start,
                                        end = end,
                                        )
                        final.save()
                
                if noDivs == 4:
                    print('Four div')
                    entriesRankedOne = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=1)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
                    entriesRankedTwo = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=2)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
                    entriesRankedThree = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=3)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
                    entriesRankedFour = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=4)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())

                    knockoutMatches = Match.objects.filter(Q(tournament=self.tournament.id) & Q(division=0))
                    final = Match.objects.filter(Q(tournament=self.tournament.id) & Q(type="Final"))
                    semis = Match.objects.filter(Q(tournament=self.tournament.id) & Q(type="Semi-Final"))
                    semisFinish = Match.objects.filter(Q(tournament=self.tournament.id) & Q(type="Semi-Final") & Q(played=True))
                    quarters = Match.objects.filter(Q(tournament=self.tournament.id) & Q(type="Quarter-Final") & Q(played=True))
                    if len(knockoutMatches) == 0:
                        #Quarters
                        for i in range(2):
                            start = str(Match.objects.filter(tournament=self.tournament.id).last().end)
                            d = datetime.datetime.strptime(start, '%H:%M:%S')     
                            d += datetime.timedelta(minutes=self.tournament.breakDuration)
                            start = d
                            d += datetime.timedelta(minutes=duration)
                            end = d

                            if i == 0:
                                quarterOne = Match(tournament = self.tournament,
                                            type = 'Quarter-Final',                  
                                            entryOne = entriesRankedOne[0],
                                            entryTwo = entriesRankedTwo[1],
                                            pitch = 1,
                                            start = start,
                                            end = end,
                                            )
                                quarterTwo = Match(tournament = self.tournament,
                                            type = 'Quarter-Final',                  
                                            entryOne = entriesRankedTwo[0],
                                            entryTwo = entriesRankedThree[1],
                                            pitch = 2,
                                            start = start,
                                            end = end,
                                            )
                            else:
                                quarterOne = Match(tournament = self.tournament,
                                            type = 'Quarter-Final',                  
                                            entryOne = entriesRankedThree[0],
                                            entryTwo = entriesRankedFour[1],
                                            pitch = 1,
                                            start = start,
                                            end = end,
                                            )
                                
                                quarterTwo = Match(tournament = self.tournament,
                                            type = 'Quarter-Final',                  
                                            entryOne = entriesRankedFour[0],
                                            entryTwo = entriesRankedOne[1],
                                            pitch = 2,
                                            start = start,
                                            end = end,
                                            )

                            quarterOne.save()
                            quarterTwo.save()
                        
                    elif (len(semis) == 0) and (len(quarters) == 4):
                        print('Semis')
                        quarters = Match.objects.filter(Q(tournament=self.tournament.id) & Q(type='Quarter-Final'))
                        quartWinners = []

                        for match in quarters:
                            if match.goalsOne > match.goalsTwo:
                                quartWin = match.entryOne
                            elif match.goalsOne < match.goalsTwo:
                                quartWin = match.entryTwo  
                            else:
                                if match.pfOne > match.pfTwo:
                                    quartWin = match.entryOne
                                else:
                                    quartWin = match.entryTwo  

                            quartWinners.append(quartWin)     

                        
                        start = str(Match.objects.filter(tournament=self.tournament.id).last().end)
                        d = datetime.datetime.strptime(start, '%H:%M:%S')     
                        d += datetime.timedelta(minutes=self.tournament.breakDuration)
                        start = d
                        d += datetime.timedelta(minutes=duration)
                        end = d    

                        semiOne = Match(tournament = self.tournament,
                                        type = 'Semi-Final',                  
                                        entryOne = quartWinners[0],
                                        entryTwo = quartWinners[1],
                                        pitch = 1,
                                        start = start,
                                        end = end,
                                    ) 
                        semiTwo = Match(tournament = self.tournament,
                                    type = 'Semi-Final',                  
                                    entryOne = quartWinners[2],
                                    entryTwo = quartWinners[3],
                                    pitch = 2,
                                    start = start,
                                    end = end,
                                )  
                            
                        semiOne.save()
                        semiTwo.save() 
                    
                    elif (len(final) == 0) and (len(semisFinish) == 2):
                        semis = Match.objects.filter(Q(tournament=self.tournament.id) & Q(type='Semi-Final'))
                        semiWinners = []

                        for match in semis:
                            if match.goalsOne > match.goalsTwo:
                                semiWin = match.entryOne
                            elif match.goalsOne < match.goalsTwo:
                                semiWin = match.entryTwo     
                            else:
                                if match.pfOne > match.pfTwo:
                                    semiWin = match.entryOne
                                else:
                                    semiWin = match.entryTwo

                            semiWinners.append(semiWin)

                        start = str(Match.objects.filter(tournament=self.tournament.id).last().end)
                        d = datetime.datetime.strptime(start, '%H:%M:%S')     
                        d += datetime.timedelta(minutes=self.tournament.breakDuration)
                        start = d
                        d += datetime.timedelta(minutes=duration)
                        end = d                                      

                        final = Match(tournament = self.tournament,
                                        type = 'Final',                  
                                        entryOne = semiWinners[0],
                                        entryTwo = semiWinners[1],
                                        pitch = 1,
                                        start = start,
                                        end = end,
                                        )
                        final.save()

                else:
                    print('invalid')

            def semis(self):
                print('semis')
                noDivs = self.tournament.noDivisions
                if noDivs == 1:
                    print('One div')
                    entriesRanked = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=1)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())

                    start = str(Match.objects.filter(tournament=self.tournament.id).last().end)
                    d = datetime.datetime.strptime(start, '%H:%M:%S')     
                    d += datetime.timedelta(minutes=self.tournament.breakDuration)
                    start = d
                    d += datetime.timedelta(minutes=duration)
                    end = d
                    
                    knockoutMatches = Match.objects.filter(Q(tournament=self.tournament.id) & Q(division=0))
                    final = Match.objects.filter(Q(tournament=self.tournament.id) & Q(type="Final"))
                    semis = Match.objects.filter(Q(tournament=self.tournament.id) & Q(type="Semi-Final") & Q(played=True))
                    if len(knockoutMatches) == 0:
                        #Semis
                        for i in range(2):
                            start = str(Match.objects.filter(tournament=self.tournament.id).last().end)
                            d = datetime.datetime.strptime(start, '%H:%M:%S')     
                            d += datetime.timedelta(minutes=self.tournament.breakDuration)
                            start = d
                            d += datetime.timedelta(minutes=duration)
                            end = d

                            if i == 0:
                                semi = Match(tournament = self.tournament,
                                            type = 'Semi-Final',                  
                                            entryOne = entriesRanked[0],
                                            entryTwo = entriesRanked[2],
                                            pitch = 1,
                                            start = start,
                                            end = end,
                                            )
                            else:
                                semi = Match(tournament = self.tournament,
                                            type = 'Semi-Final',                  
                                            entryOne = entriesRanked[1],
                                            entryTwo = entriesRanked[3],
                                            pitch = 1,
                                            start = start,
                                            end = end,
                                            )
                            semi.save()
                        
                    elif (len(final) == 0) and (len(semis) == 2) :
                        print('Finals & 3rd/4th')
                        #Final & 3rd/4th Playoff
                        semis = Match.objects.filter(Q(tournament=self.tournament.id) & Q(type='Semi-Final'))
                        semiWinners = []
                        semiLosers = []

                        for match in semis:
                            if match.goalsOne > match.goalsTwo:
                                semiWin = match.entryOne
                                semiLoss = match.entryTwo

                            elif match.goalsOne < match.goalsTwo:
                                semiWin = match.entryTwo                                                            
                                semiLoss = match.entryOne

                            else:
                                if match.pfOne > match.pfTwo:
                                    semiWin = match.entryOne
                                    semiLoss = match.entryTwo
                                else:
                                    semiWin = match.entryTwo 
                                    semiLoss = match.entryOne  

                            semiWinners.append(semiWin)
                            semiLosers.append(semiLoss)                                                   

                        final = Match(tournament = self.tournament,
                                        type = 'Final',                  
                                        entryOne = semiWinners[0],
                                        entryTwo = semiWinners[1],
                                        pitch = 1,
                                        start = start,
                                        end = end,
                                        )
                        
                        final.save()

                if noDivs == 2:
                    entriesRankedOne = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=1)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
                    entriesRankedTwo = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=2)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
                    print('Two div')

                    start = str(Match.objects.filter(tournament=self.tournament.id).last().end)
                    d = datetime.datetime.strptime(start, '%H:%M:%S')     
                    d += datetime.timedelta(minutes=self.tournament.breakDuration)
                    start = d
                    d += datetime.timedelta(minutes=duration)
                    end = d
                    
                    knockoutMatches = Match.objects.filter(Q(tournament=self.tournament.id) & Q(division=0))
                    final = Match.objects.filter(Q(tournament=self.tournament.id) & Q(type="Final"))
                    semis = Match.objects.filter(Q(tournament=self.tournament.id) & Q(type="Semi-Final") & Q(played=True))
                    if len(knockoutMatches) == 0:
                        #Semis
                        for i in range(2):
                            start = str(Match.objects.filter(tournament=self.tournament.id).last().end)
                            d = datetime.datetime.strptime(start, '%H:%M:%S')     
                            d += datetime.timedelta(minutes=self.tournament.breakDuration)
                            start = d
                            d += datetime.timedelta(minutes=duration)
                            end = d

                            if i == 0:
                                semi = Match(tournament = self.tournament,
                                            type = 'Semi-Final',                  
                                            entryOne = entriesRankedOne[0],
                                            entryTwo = entriesRankedTwo[1],
                                            pitch = 1,
                                            start = start,
                                            end = end,
                                            )
                            else:
                                semi = Match(tournament = self.tournament,
                                            type = 'Semi-Final',                  
                                            entryOne = entriesRankedOne[1],
                                            entryTwo = entriesRankedTwo[0],
                                            pitch = 1,
                                            start = start,
                                            end = end,
                                            )
                            semi.save()

                    elif (len(final) == 0) and (len(semis) == 2):
                        print('Finals & 3rd/4th')
                        #Final & 3rd/4th Playoff
                        semis = Match.objects.filter(Q(tournament=self.tournament.id) & Q(type='Semi-Final'))
                        semiWinners = []
                        semiLosers = []

                        for match in semis:
                            if match.goalsOne > match.goalsTwo:
                                semiWin = match.entryOne
                                semiLoss = match.entryTwo

                            elif match.goalsOne < match.goalsTwo:
                                semiWin = match.entryTwo                                                            
                                semiLoss = match.entryOne

                            else:
                                if match.pfOne > match.pfTwo:
                                    semiWin = match.entryOne
                                    semiLoss = match.entryTwo
                                else:
                                    semiWin = match.entryTwo 
                                    semiLoss = match.entryOne  

                            semiWinners.append(semiWin)
                            semiLosers.append(semiLoss)                                                   

                        final = Match(tournament = self.tournament,
                                        type = 'Final',                  
                                        entryOne = semiWinners[0],
                                        entryTwo = semiWinners[1],
                                        pitch = 1,
                                        start = start,
                                        end = end,
                                        )
                        
                        final.save()

                if noDivs == 4:
                    print('Four div')
                    entriesRankedOne = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=1)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
                    entriesRankedTwo = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=2)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
                    entriesRankedThree = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=3)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
                    entriesRankedFour = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=4)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())

                    knockoutMatches = Match.objects.filter(Q(tournament=self.tournament.id) & Q(division=0))
                    final = Match.objects.filter(Q(tournament=self.tournament.id) & Q(type="Final"))
                    semis = Match.objects.filter(Q(tournament=self.tournament.id) & Q(type="Semi-Final") & Q(played=True))
                    if len(knockoutMatches) == 0:
                        #Semis
                        for i in range(2):
                            start = str(Match.objects.filter(tournament=self.tournament.id).last().end)
                            d = datetime.datetime.strptime(start, '%H:%M:%S')     
                            d += datetime.timedelta(minutes=self.tournament.breakDuration)
                            start = d
                            d += datetime.timedelta(minutes=duration)
                            end = d

                            if i == 0:
                                semi = Match(tournament = self.tournament,
                                            type = 'Semi-Final',                  
                                            entryOne = entriesRankedOne[0],
                                            entryTwo = entriesRankedThree[0],
                                            pitch = 1,
                                            start = start,
                                            end = end,
                                            )
                            else:
                                semi = Match(tournament = self.tournament,
                                            type = 'Semi-Final',                  
                                            entryOne = entriesRankedTwo[0],
                                            entryTwo = entriesRankedFour[0],
                                            pitch = 2,
                                            start = start,
                                            end = end,
                                            )
                            semi.save()
                        
                    elif (len(final) == 0) and (len(semis) == 2):
                        print('Finals')
                        #Final
                        semis = Match.objects.filter(Q(tournament=self.tournament.id) & Q(type='Semi-Final'))
                        semiWinners = []
                        semiLosers = []

                        start = str(Match.objects.filter(tournament=self.tournament.id).last().end)
                        d = datetime.datetime.strptime(start, '%H:%M:%S')     
                        d += datetime.timedelta(minutes=self.tournament.breakDuration)
                        start = d
                        d += datetime.timedelta(minutes=duration)
                        end = d

                        for match in semis:
                            if match.goalsOne > match.goalsTwo:
                                semiWin = match.entryOne
                            elif match.goalsOne < match.goalsTwo:
                                semiWin = match.entryTwo
                            else:
                                if match.pfOne > match.pfTwo:
                                    semiWin = match.entryOne
                                else:
                                    semiWin = match.entryTwo 

                            semiWinners.append(semiWin)                                                

                        final = Match(tournament = self.tournament,
                                        type = 'Final',                  
                                        entryOne = semiWinners[0],
                                        entryTwo = semiWinners[1],
                                        pitch = 1,
                                        start = start,
                                        end = end,
                                        )
                        
                        final.save()

                else:
                    print('invalid')

            def final(self):
                print('final')
                noDivs = self.tournament.noDivisions
                noDivs = self.tournament.noDivisions
                if noDivs == 1:
                    print('One div')
                    entriesRanked = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=1)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
                    
                    start = str(Match.objects.filter(tournament=self.tournament.id).last().end)
                    d = datetime.datetime.strptime(start, '%H:%M:%S')     
                    d += datetime.timedelta(minutes=self.tournament.breakDuration)
                    start = d
                    d += datetime.timedelta(minutes=duration)
                    end = d
                    
                    final = Match.objects.filter(Q(tournament=self.tournament.id) & Q(type="Final"))
                    if len(final) == 0:

                        final = Match(tournament = self.tournament,
                                        type = 'Final',                  
                                        entryOne = entriesRanked[0],
                                        entryTwo = entriesRanked[1],
                                        pitch = 1,
                                        start = start,
                                        end = end,
                                        )
                        
                        final.save()

                if noDivs == 2:
                    print('Two divs')
                    entriesRankedOne = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=1)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
                    entriesRankedTwo = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=2)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())

                    start = str(Match.objects.filter(tournament=self.tournament.id).last().end)
                    d = datetime.datetime.strptime(start, '%H:%M:%S')     
                    d += datetime.timedelta(minutes=self.tournament.breakDuration)
                    start = d
                    d += datetime.timedelta(minutes=duration)
                    end = d
                    
                    final = Match.objects.filter(Q(tournament=self.tournament.id) & Q(type="Final"))
                    if len(final) == 0:

                        final = Match(tournament = self.tournament,
                                        type = 'Final',                  
                                        entryOne = entriesRankedOne[0],
                                        entryTwo = entriesRankedTwo[0],
                                        pitch = 1,
                                        start = start,
                                        end = end,
                                        )
                        
                        final.save()
                else:
                    print('invalid')

#--------------------------------------------------------------------------------------------------
#Main Program
#--------------------------------------------------------------------------------------------------

            print('updating')

            #User Inputs
            tourn = self.instance.tournament
            match = self.instance
            entryOne = self.instance.entryOne
            entryTwo = self.instance.entryTwo
            played = self.instance.played

            if match.division == 0:
                if played == True:
                    ranking(entryOne, entryTwo, match)
            else:
                if self.prevMatch.played == True:
                    prevResults(entryOne, entryTwo, self.prevMatch)
                    if played == True:
                        validResults(entryOne, entryTwo, match)

                elif played == True:
                    validResults(entryOne, entryTwo, match)

            noPlayedMatches = Match.objects.filter(Q(tournament=tourn.id) & Q(played=True)).count()
            matches = Match.objects.filter(Q(tournament=tourn.id) & ~Q(division=0))
            matchCount = 0
            for match in matches:
                if not(match.entryOne == match.entryTwo):
                    matchCount += 1

            if (noPlayedMatches >= matchCount):
                print("KNOCKOUTS!")
                if tourn.matchType == "Each Way":
                    duration = (2 * tourn.matchDuration) + tourn.halftimeDuration
                else:
                    duration = tourn.matchDuration

                if tourn.knockoutRounds == "Playoffs, Semis & Final":
                    playoffs(self.instance, duration)
                elif tourn.knockoutRounds == "Semis & Final":
                    semis(self.instance)
                elif tourn.knockoutRounds == "Final":
                    final(self.instance)
                else:
                    print("no knockout rounds")
                    if played == True:
                        tournament = Tournament.objects.get(pk=tourn.id)
                        tournament.finished = True
                        tournament.save()

                if self.instance.type == "Final" and played == True:
                    tournament = Tournament.objects.get(pk=tourn.id)
                    tournament.finished = True
                    tournament.save()
                    print('finished')


        except Exception as e:
            print(e)