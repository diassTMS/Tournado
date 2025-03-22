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
                knockoutMatches = Match.objects.filter(Q(tournament=self.tournament.id) & Q(division=0))
                final = Match.objects.get(Q(tournament=self.tournament.id) & Q(type="Final"))
                semis = list(Match.objects.filter(Q(tournament=self.tournament.id) & Q(type="Semi-Final")))
                semisPlayed = Match.objects.filter(Q(tournament=self.tournament.id) & Q(type="Semi-Final") & Q(played=True))
                quarters = list(Match.objects.filter(Q(tournament=self.tournament.id) & Q(type="Quarter-Final")))
                quartersPlayed = Match.objects.filter(Q(tournament=self.tournament.id) & Q(type="Quarter-Final") & Q(played=True))
                playoffs = Match.objects.filter(Q(tournament=self.tournament.id) & Q(division=0) & ~Q(type="Free") & ~Q(type="Final") & ~Q(type="Semi-Final") & ~Q(type="3rd/4th Playoff"))
                thirdFourth = Match.objects.get(Q(tournament=self.tournament.id) & Q(type="3rd/4th Playoff"))

                if noDivs == 1:
                    print('One div')
                    entriesRanked = Entry.objects.filter(Q(tournament=self.tournament.id) & Q(division=1)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())

                    for i in range(len(knockoutMatches)):
                        teamOne = entriesRanked[(2*i)]
                        teamTwo = entriesRanked[(2*i + 1)]

                        playoff = knockoutMatches[i]            
                        playoff.entryOne = teamOne
                        playoff.entryTwo = teamTwo
                        playoff.save()

                elif noDivs == 2:
                    print('Two div')
                    entriesRankedOne = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=1)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
                    entriesRankedTwo = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=2)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
                   
                    if semis[0].entryOne == semis[0].entryTwo:
                        semis[0].entryOne = entriesRankedOne[0]
                        print(entriesRankedOne[0])
                        print(entriesRankedTwo[1])
                        semis[0].entryTwo = entriesRankedTwo[1]
                        
                        semis[0].save()

                    if semis[1].entryOne == semis[1].entryTwo:
                        semis[1].entryOne = entriesRankedOne[1]
                        semis[1].entryTwo = entriesRankedTwo[0]
                        
                        semis[1].save()
                        
                    #Playoffs
                    for i in range(len(playoffs)):
                        teamOne = entriesRankedOne[2 + i]
                        teamTwo = entriesRankedTwo[2 + i]
                        
                        playoff = playoffs[i] 
                        print(playoff.type)                 
                        playoff.entryOne = teamOne
                        playoff.entryTwo = teamTwo
                        playoff.save()

                    if ((final.entryOne == final.entryTwo) or (thirdFourth.entryOne == thirdFourth.entryTwo)) and (len(semisPlayed) == 2):
                        print('Finals & 3rd/4th')
                        semiWinners = []
                        semiLosers = []

                        for match in semisPlayed:
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

                        thirdFourth.entryOne = semiLosers[0]
                        thirdFourth.entryTwo = semiLosers[1]
                        thirdFourth.save() 

                        final.entryOne = semiWinners[0]
                        final.entryTwo = semiWinners[1]
                        final.save()
                
                elif noDivs == 4:
                    print('Four div')
                    entriesRankedOne = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=1)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
                    entriesRankedTwo = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=2)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
                    entriesRankedThree = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=3)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
                    entriesRankedFour = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=4)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())

                    #Quarters
                    if quarters[0].entryOne == quarters[0].entryTwo:
                        quarterOne = quarters[0]                
                        quarterOne.entryOne = entriesRankedOne[0]
                        quarterOne.entryTwo = entriesRankedTwo[1]
                        quarterOne.save()

                        quarterTwo = quarters[1]
                        quarterTwo.entryOne = entriesRankedTwo[0]
                        quarterTwo.entryTwo = entriesRankedThree[1]
                        quarterTwo.save()

                        quarterThree = quarters[2]                 
                        quarterThree.entryOne = entriesRankedThree[0]
                        quarterThree.entryTwo = entriesRankedFour[1]
                        quarterThree.save()
                                
                        quarterFour = quarters[3]
                        quarterFour.entryOne = entriesRankedFour[0]
                        quarterFour.entryTwo = entriesRankedOne[1]
                        quarterFour.save()

                        
                    
                    if (len(semisPlayed) == 0) and (len(quartersPlayed) == 4):
                        print('Semis')
                        quartWinners = []

                        for match in quartersPlayed:
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

                        if semis[0].entryOne == semis[0].entryTwo:
                            semis[0].entryOne = quartWinners[0]
                            semis[0].entryTwo = quartWinners[1]
                            semis[0].save()

                        if semis[1].entryOne == semis[1].entryTwo:
                            semis[1].entryOne = quartWinners[2]
                            semis[1].entryTwo = quartWinners[3]
                            semis[1].save()
                    
                    elif (final.entryOne == final.entryTwo) and (len(semisPlayed) == 2):
                        semiWinners = []
                        semiLosers = []

                        for match in semisPlayed:
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

                        thirdFourth.entryOne = semiLosers[0]
                        thirdFourth.entryTwo = semiLosers[1]
                        thirdFourth.save()                                  

                        final.entryOne = semiWinners[0]
                        final.entryTwo = semiWinners[1]
                        final.save()

                else:
                    print('invalid')

            def semis(self):
                print('semis')
                noDivs = self.tournament.noDivisions
                final = Match.objects.get(Q(tournament=self.tournament.id) & Q(type="Final"))
                semi = list(Match.objects.filter(Q(tournament=self.tournament.id) & Q(type="Semi-Final")))
                semisPlayed = Match.objects.filter(Q(tournament=self.tournament.id) & Q(type="Semi-Final") & Q(played=True))
                
                if noDivs == 1:
                    print('One div')
                    entriesRanked = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=1)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())

                    if semi[0].entryOne == semi[0].entryTwo:
                        semi[0].entryOne = entriesRanked[0]
                        semi[0].entryTwo = entriesRanked[2]
                        
                        semi[0].save()

                    if semi[1].entryOne == semi[1].entryTwo:
                        semi[1].entryOne = entriesRanked[1]
                        semi[1].entryTwo = entriesRanked[3]
                        
                        semi[1].save()

                elif noDivs == 2:
                    print('Two div')
                    entriesRankedOne = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=1)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
                    entriesRankedTwo = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=2)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
                   
                    if semi[0].entryOne == semi[0].entryTwo:
                        semi[0].entryOne = entriesRankedOne[0]
                        semi[0].entryTwo = entriesRankedTwo[1]
                        
                        semi[0].save()

                    if semi[1].entryOne == semi[1].entryTwo:
                        semi[1].entryOne = entriesRankedOne[1]
                        semi[1].entryTwo = entriesRankedTwo[0]
                        
                        semi[1].save()

                elif noDivs == 4:
                    print('Four div')
                    entriesRankedOne = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=1)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
                    entriesRankedTwo = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=2)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
                    entriesRankedThree = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=3)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
                    entriesRankedFour = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=4)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
                    
                    if semi[0].entryOne == semi[0].entryTwo:
                        semi[0].entryOne = entriesRankedOne[0]
                        semi[0].entryTwo = entriesRankedTwo[0]
                        
                        semi[0].save()

                    if semi[1].entryOne == semi[1].entryTwo:
                        semi[1].entryOne = entriesRankedThree[0]
                        semi[1].entryTwo = entriesRankedFour[0]
                        
                        semi[1].save()

                else:
                    print('invalid')

                if (final.entryOne == final.entryTwo) and (len(semisPlayed) == 2):
                    semiWinners = []
                    semiLosers = []

                    for match in semisPlayed:
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

                    final.entryOne = semiWinners[0]
                    final.entryTwo = semiWinners[1]
                    final.save()

            def final(self):
                print('final')
                noDivs = self.tournament.noDivisions

                if noDivs == 1:
                    print('One div')
                    entriesRanked = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=1)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
                    
                    final = Match.objects.get(Q(tournament=self.tournament.id) & Q(type="Final"))
                    if final.entryOne == final.entryTwo:
                        final.entryOne = entriesRanked[0]
                        final.entryTwo = entriesRanked[1]
                        final.save()

                elif noDivs == 2:
                    print('Two divs')
                    entriesRankedOne = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=1)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
                    entriesRankedTwo = Entry.objects.filter(Q(tournament=self.tournament) & Q(division=2)).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())

                    final = Match.objects.get(Q(tournament=self.tournament.id) & Q(type="Final"))
                    if final.entryOne == final.entryTwo:
                        final.entryOne = entriesRankedOne[0]
                        final.entryTwo = entriesRankedTwo[0]
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
                    print('ranking', entryOne, entryTwo, match)
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