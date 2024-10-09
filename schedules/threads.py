#-----------------------------------------------------------------------------------------
#Libraries
#-----------------------------------------------------------------------------------------

import numpy as np
import math
import random
import threading
from tournaments.models  import Entry, Match, Tournament
from leagues.models import League, LeagueEntry, LeagueMatch
from django.contrib import messages
from ast import literal_eval
import datetime
from django.db.models import Q
from django.contrib.auth.models import User

class GenerateScheduleThread(threading.Thread):
    def __init__(self, instance):
        self.instance = instance
        threading.Thread.__init__(self)

    def run(self):
        try:
#-----------------------------------------------------------------------------------------
#Global Variables
#-----------------------------------------------------------------------------------------

            entriesData = []
            optimumSchedule = []
            efficiency = []
            UmpireSchedule = []
            scheduled = False
            optimum = False
            x = 0
            y = 0
            stanDev = 99
            increase = 0
            MAX = 10000

#--------------------------------------------------------------------------------------------------
#Sub Programs
#--------------------------------------------------------------------------------------------------

            def indexCalc(pSchedule, pEntries, pDivs):
                divMatches = []
                index = []
                score = []
                length = len(pSchedule)
                pitch = len(pSchedule[0])
                
                divisions = divisionCalc(pDivs, pEntries)
                divMatches = divMatchesCalc(divisions)
                    
                for i in range (pEntries):
                    backtoback = 0
                    gamesOff = []
                    points = 0
                    
                    for j in range(length):
                        
                        rowUpOne = []
                        rowCurrent = []
                        
                        for k in range(pitch):
                            if j > 0:
                                rowUpOne += pSchedule[j-1][k]
                            rowCurrent += pSchedule[j][k]
                            
                            if (pDivs > 1) and (pitch == pDivs) and not(pSchedule[j][k] in divMatches[k]):
                                points += 2
                        
                        if (i+1) in rowCurrent:
                            if (i+1) in rowUpOne:
                                backtoback += 1
                            gamesOff.append(0)
                        else:
                            gamesOff.append(1)
                            
                    
                    points += (backtoback*5)
                    
                    temp = gamesOff[0]
                    count = 0
                    while count < len(gamesOff):
                        row = 0
                        temp = gamesOff[count]
                        if temp == 0:
                            count += 1
                        else:
                            while temp != 0 and count != len(gamesOff):
                                row += 1
                                count += 1
                                if (count) == len(gamesOff):
                                    continue
                                else:
                                    temp = gamesOff[count]
                                
                            count += 1
                            if row > 1:
                                points += (row*2)
                    
                    index.append(points)
                            
                std = np.std(index)
                mean = np.mean(index)
                score.append(std)
                score.append(mean)
                
                return score


            def divisionCalc(pNoPools, pNoEntries):
                index = 0
                divisions = []
                while index < pNoPools:
                    div = []
                    entries = list(range(1, pNoEntries+1))
                    teams = entries[(index)::(pNoPools)]
                    div.append(index+1)
                    div.append(teams)
                    
                    divisions.append(div)
                    index += 1

                return divisions

            def divMatchesCalc(pDivisions):
                matches = []
                for index in range(0,len(pDivisions)):
                    pArray = pDivisions[index][1]
                    pCombinations = []
                    aTemps = []

                    pLength = len(pArray)

                    for i in range(pLength-1):
                        for j in range(0, pLength-i-1):
                            combination = pArray[0:2]  
                            pCombinations.append(combination) 
                                
                            temp = pArray[1]
                            del pArray[1]
                            pArray.append(temp)
                            
                        
                        aTemps.append(pArray[0])
                        del pArray[0]
                        
                    matches.append(pCombinations)
                
                return matches
                
            def matchesCalc(pDivisions):
                pMatchlist = []
                matches = []
                for index in range(0,len(pDivisions)):
                    pArray = pDivisions[index][1]
                    pCombinations = []
                    aTemps = []

                    pLength = len(pArray)

                    for i in range(pLength-1):
                        for j in range(0, pLength-i-1):
                            combination = pArray[0:2]  
                            pCombinations.append(combination) 
                                
                            temp = pArray[1]
                            del pArray[1]
                            pArray.append(temp)
                            
                        
                        aTemps.append(pArray[0])
                        del pArray[0]
                        
                    matches.append(pCombinations)
                
                for i in range(len(matches)):
                    for j in range(len(matches[i])):
                        pMatchlist.append(matches[i][j])
                
                return pMatchlist

            def createArray(pPitches, pLength):
                pArray = []
                for i in range(pLength):
                        pArray.append([])
                        
                for i in range(pLength):
                    for j in range(pPitches):
                        pArray[i].append([])
                        
                return pArray

            def schedule(pLen, pPitch, pArr, pList):
                for i in range(pLen):
                    for j in range(pPitch):
                        
                        rowUpOne = []
                        rowUpTwo = []
                        rowCurrent = []
                        
                        for k in range(pPitch):
                            if i > 1:
                                rowUpOne += pArr[i-1][k]
                                rowUpTwo += pArr[i-2][k]
                            elif i > 0:
                                rowUpOne += pArr[i-1][k]
                                    
                            rowCurrent += pArr[i][k]
                        
                        count = 0
                        while pArr[i][j] == []:
                            #Check if end of matchlist reached
                            if count == len(pList):
                                pArr[i][j] = [0, 0]
                            else:
                            #Check if match teams are currently playing
                                if not((pList[count][0] in rowCurrent) or (pList[count][1] in rowCurrent)):
                                    #Check for both teams that there will not be a three in a row
                                    if (not((pList[count][0] in rowUpOne) and (pList[count][0] in rowUpTwo))) and (not((pList[count][1] in rowUpOne) and (pList[count][1] in rowUpTwo))):
                                        pArr[i][j] = pList[count]
                                        del pList[count]
                                    else:
                                        count += 1
                                else:
                                    count += 1
                leftOver = len(pList)
                return pArr, leftOver
            
            def umpires(schedule, umpires, nPitch, data):
                arr = createArray(nPitch, len(schedule))                
                count = 0
                for i in range(len(schedule)):
                    for j in range(nPitch):
                
                        users = []
                        for l in range(2):
                            user = Entry.objects.get(Q(tournament=self.instance) & Q(pk=data[(schedule[i][j][l])-1][0].id)).user
                            if not(user.groups.filter(name="Admin").exists()):
                                users.append(user)
                        
                        rowCurrent = []
                        for k in range(nPitch):
                            rowCurrent += arr[i][k]

                        while len(arr[i][j]) != 2:
                            match = schedule[i][j]
                            entry = Entry.objects.get(Q(tournament=self.instance) & Q(pk=data[(umpires[count]-1)][0].id))

                            if match == [0,0]:
                                arr[i][j] = [0,0]
                            else:
                                if not(entry.umpire in match) and not(entry.umpire in rowCurrent) and not(entry.user in users):
                                    if entry.umpire in arr[i][j]:
                                        arr[i][j].append('Ind.')
                                    else:
                                        arr[i][j].append(entry.umpire)
                                    
                                if count == (len(umpires)-1):
                                    count = 0
                                else:
                                    count += 1
                
                return arr

#--------------------------------------------------------------------------------------------------
#Main Program
#--------------------------------------------------------------------------------------------------


            print('Execution started')
            if self.instance.generatedSchedule == True:
                print('deleting prev matches')
                try:
                    matches = Match.objects.filter(tournament=self.instance).delete()
                    entriesPrev = Entry.objects.filter(tournament=self.instance)
                    tourn = Tournament.objects.get(pk=self.instance.id)
                    if tourn.finished == True:
                        tourn.finished = False
                        tourn.save()
                    
                    for entryPrev in entriesPrev:
                        entryPrev.points = 0
                        entryPrev.won = 0
                        entryPrev.drawn = 0
                        entryPrev.lost = 0
                        entryPrev.forGoals = 0
                        entryPrev.againstGoals = 0
                        entryPrev.goalDiff = 0
                        entryPrev.played = 0
                        entryPrev.save()
                except:
                    print('already generated but no data')

            print('updating')

            #User Inputs
            noEntries = self.instance.noTeams
            noDivs = self.instance.noDivisions
            noPitches = self.instance.noPitches
            start = str(self.instance.startTime)
            match_duration = self.instance.matchDuration
            break_duration = self.instance.breakDuration
            halftime_duration = self.instance.halftimeDuration

            #Mapping entries
            entries = Entry.objects.filter(tournament=self.instance).order_by('rank')
            for entry in entries:
                row = []
                row.append(entry)
                entriesData.append(row)

            #Splitting entries into different divisions
            divisions = divisionCalc(noDivs, noEntries)
            #Updating entry divisions
            for i in range(len(divisions)):
                for j in range(len(divisions[i][1])-1):
                    #Don't question line 264-265. They work!
                    entriesData[(divisions[i][1][j])-1].append(divisions[i][0])
                    entry = Entry.objects.get(Q(tournament=self.instance) & Q(pk=entriesData[(divisions[i][1][j])-1][0].id))
                    entry.division = divisions[i][0]
                    entry.save()
            #Creating a list of all division matches that need to be played
            matches = matchesCalc(divisions)

            while optimum == False and x < (MAX+1):
                
                divisions = []
                matches = []
                array = []
                length = 0
                
                divisions = divisionCalc(noDivs, noEntries)
                matches = matchesCalc(divisions)
                
                if x == MAX:
                    increase += 1
                    x = 0
                
                length = math.ceil(len(matches) / noPitches) + increase
                
                if x > 0:
                    random.shuffle(matches)
                    
                array = createArray(noPitches, length)
                OOP, missing = schedule(length, noPitches, array, matches)
                
                if scheduled == False:
                    if missing == 0:
                        optimumSchedule = OOP
                        efficiency = indexCalc(optimumSchedule, noEntries, noDivs)
                        scheduled = True
                else:
                    if (x+1) == MAX:
                        optimum = True
                    else:
                        if missing == 0:
                            newEfficiency = indexCalc(OOP, noEntries, noDivs)
                            if newEfficiency[1] < efficiency[1]:
                                optimumSchedule = OOP
                                efficiency = newEfficiency
                
                x += 1

            if self.instance.umpires == True:
                #Generating Umpire Schedule
                while y < 20:
                    umps = []
                    for i in range(noEntries):
                        umps.append(i+1)
                    
                    random.shuffle(umps)
                    umpArr = umpires(optimumSchedule, umps, noPitches, entriesData)
                    
                    num = []
                    for j in range(noEntries):
                        count = 0
                        umpire = Entry.objects.get(Q(tournament=self.instance) & Q(pk=entriesData[j][0].id)).umpire
                        for k in range(len(umpArr)):
                            for l in range(len(umpArr[k])):
                                if umpire in umpArr[k][l]:
                                    count += 1
                        
                        num.append(count)

                    if np.std(num) < stanDev:
                        stanDev = np.std(num)
                        UmpireSchedule = umpArr
                    
                    y += 1
            
            print(stanDev)
            print(optimumSchedule)
            #Creating Matches
            for i in range(len(optimumSchedule)):
                for j in range(len(optimumSchedule[i])):
                    print('i', i, 'j',j)
                    if not(optimumSchedule[i][j] == [0,0]):
                        if self.instance.matchType == "One Way":
                            duration = match_duration + break_duration
                            if self.instance.umpires == True:
                                match = Match(tournament = self.instance,
                                                division = int(entriesData[(optimumSchedule[i][j][0])-1][1]),                  
                                                entryOne = Entry.objects.get(Q(tournament=self.instance) & Q(pk=entriesData[(optimumSchedule[i][j][0])-1][0].id)),
                                                entryTwo = Entry.objects.get(Q(tournament=self.instance) & Q(pk=entriesData[(optimumSchedule[i][j][1])-1][0].id)),
                                                pitch = j+1,
                                                start = datetime.datetime.strptime(start, '%H:%M:%S') + datetime.timedelta(minutes=(duration * i)),
                                                end = datetime.datetime.strptime(start, '%H:%M:%S') + datetime.timedelta(minutes=(match_duration + (duration * i))),
                                                umpireOne = UmpireSchedule[i][j][0],
                                                umpireTwo = UmpireSchedule[i][j][1],
                                                )
                                match.save()
                            else:
                                match = Match(tournament = self.instance,
                                                division = int(entriesData[(optimumSchedule[i][j][0])-1][1]),                  
                                                entryOne = Entry.objects.get(Q(tournament=self.instance) & Q(pk=entriesData[(optimumSchedule[i][j][0])-1][0].id)),
                                                entryTwo = Entry.objects.get(Q(tournament=self.instance) & Q(pk=entriesData[(optimumSchedule[i][j][1])-1][0].id)),
                                                pitch = j+1,
                                                start = datetime.datetime.strptime(start, '%H:%M:%S') + datetime.timedelta(minutes=(duration * i)),
                                                end = datetime.datetime.strptime(start, '%H:%M:%S') + datetime.timedelta(minutes=(match_duration + (duration * i))),
                                                )
                                match.save()
                        else:
                            full_match_duration = (2 * match_duration) + halftime_duration
                            duration = full_match_duration + break_duration
                            if self.instance.umpires == True:
                                match = Match(tournament = self.instance,
                                            division = int(entriesData[(optimumSchedule[i][j][0])-1][1]),                  
                                            entryOne = Entry.objects.get(Q(tournament=self.instance) & Q(pk=entriesData[(optimumSchedule[i][j][0])-1][0].id)),
                                            entryTwo = Entry.objects.get(Q(tournament=self.instance) & Q(pk=entriesData[(optimumSchedule[i][j][1])-1][0].id)),
                                            pitch = j+1,
                                            start = datetime.datetime.strptime(start, '%H:%M:%S') + datetime.timedelta(minutes=(duration * i)),
                                            end = datetime.datetime.strptime(start, '%H:%M:%S') + datetime.timedelta(minutes=(full_match_duration + (duration * i))),
                                            umpireOne = UmpireSchedule[i][j][0],
                                            umpireTwo = UmpireSchedule[i][j][1],
                                            )
                                match.save()
                            else:
                                match = Match(tournament = self.instance,
                                            division = int(entriesData[(optimumSchedule[i][j][0])-1][1]),                  
                                            entryOne = Entry.objects.get(Q(tournament=self.instance) & Q(pk=entriesData[(optimumSchedule[i][j][0])-1][0].id)),
                                            entryTwo = Entry.objects.get(Q(tournament=self.instance) & Q(pk=entriesData[(optimumSchedule[i][j][1])-1][0].id)),
                                            pitch = j+1,
                                            start = datetime.datetime.strptime(start, '%H:%M:%S') + datetime.timedelta(minutes=(duration * i)),
                                            end = datetime.datetime.strptime(start, '%H:%M:%S') + datetime.timedelta(minutes=(full_match_duration + (duration * i))),
                                            )
                                match.save()
                    #Free Match
                    else:
                        if self.instance.matchType == "One Way":
                            duration = match_duration + break_duration
                            match = Match(tournament = self.instance,
                                            division = -1,
                                            entryOne = Entry.objects.get(Q(tournament=self.instance) & Q(pk=entriesData[0][0].id)),
                                            entryTwo = Entry.objects.get(Q(tournament=self.instance) & Q(pk=entriesData[0][0].id)),
                                            pitch = j+1,
                                            start = datetime.datetime.strptime(start, '%H:%M:%S') + datetime.timedelta(minutes=(duration * i)),
                                            end = datetime.datetime.strptime(start, '%H:%M:%S') + datetime.timedelta(minutes=(match_duration + (duration * i))),
                                            )
                            match.save()
                        else:
                            full_match_duration = (2 * match_duration) + halftime_duration
                            duration = full_match_duration + break_duration
                            match = Match(tournament = self.instance,
                                            division = -1,
                                            entryOne = Entry.objects.get(Q(tournament=self.instance) & Q(pk=entriesData[0][0].id)),
                                            entryTwo = Entry.objects.get(Q(tournament=self.instance) & Q(pk=entriesData[0][0].id)),
                                            pitch = j+1,
                                            start = datetime.datetime.strptime(start, '%H:%M:%S') + datetime.timedelta(minutes=(duration * i)),
                                            end = datetime.datetime.strptime(start, '%H:%M:%S') + datetime.timedelta(minutes=(full_match_duration + (duration * i))),
                                            )
                            match.save()
            
            print('generated')
            generated = True
            Tournament.objects.filter(pk=self.instance.id).update(generatedSchedule=generated)

        except Exception as e:
            print(e)

#LEAGUES

class GenerateLeagueScheduleThread(threading.Thread):
    def __init__(self, instance):
        self.instance = instance
        threading.Thread.__init__(self)

    def run(self):
        try:

            print('Execution started')
            if self.instance.generatedSchedule == True:
                print('deleting prev matches')
                matches = LeagueMatch.objects.filter(league=self.instance).delete()
                entriesPrev = LeagueEntry.objects.filter(league=self.instance)
                for entryPrev in entriesPrev:
                    entryPrev.points = 0
                    entryPrev.won = 0
                    entryPrev.drawn = 0
                    entryPrev.lost = 0
                    entryPrev.forGoals = 0
                    entryPrev.againstGoals = 0
                    entryPrev.goalDiff = 0
                    entryPrev.played = 0
                    entryPrev.save()

            print('updating')
            noTeams = self.instance.noTeams
            entries = LeagueEntry.objects.filter(league=self.instance)
            divisions = []
            for k in range(noTeams):
                divisions.append(k+1)
            
            matches = []
            aTemps = []
            pLength = len(divisions)

            for i in range(pLength-1):
                for j in range(0, pLength-i-1):
                    combination = divisions[0:2]  
                    matches.append(combination) 
                        
                    temp = divisions[1]
                    del divisions[1]
                    divisions.append(temp)
                    
                
                aTemps.append(divisions[0])
                del divisions[0]


            for match in matches:
                match = LeagueMatch(league = self.instance,
                              entryOne = LeagueEntry.objects.get(Q(league=self.instance) & Q(pk=entries[(match[0]-1)].id)),
                              entryTwo = LeagueEntry.objects.get(Q(league=self.instance) & Q(pk=entries[(match[1]-1)].id)),
                              )
                match.save()

            print('generated')
            generated = True
            League.objects.filter(pk=self.instance.id).update(generatedSchedule=generated)
            
        except Exception as e:
            print(e)
