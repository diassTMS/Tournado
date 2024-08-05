import numpy as np
import threading
from .models  import LeagueEntry, LeagueMatch, League
from django.db.models import Q

class LeagueEntryUpdateThread(threading.Thread):
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

#--------------------------------------------------------------------------------------------------
#Main Program
#--------------------------------------------------------------------------------------------------

            print('updating')

            #User Inputs
            league = self.instance.league
            match = self.instance
            entryOne = self.instance.entryOne
            entryTwo = self.instance.entryTwo
            played = self.instance.played

            if self.prevMatch.played == True:
                prevResults(entryOne, entryTwo, self.prevMatch)
                if played == True:
                    validResults(entryOne, entryTwo, match)

            elif played == True:
                validResults(entryOne, entryTwo, match)

            noPlayedMatches = LeagueMatch.objects.filter(Q(league=league.id) & Q(played=True)).count()
            matches = LeagueMatch.objects.filter(league=league.id).count()
            if matches == noPlayedMatches:
                league.finished = True
                league.save()

        except Exception as e:
            print(e)