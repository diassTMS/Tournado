#-----------------------------------------------------------------------------------------
#Libraries
#-----------------------------------------------------------------------------------------

import numpy as np
import math
import random
import threading
from tournaments.models  import Entry, Match, Tournament
from schedules.models import PitchNames, Schedule
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
            MAX = 100

#--------------------------------------------------------------------------------------------------
#Sub Programs
#--------------------------------------------------------------------------------------------------

            def indexCalc(pSchedule, pEntries, pDivs):
                divMatches = []
                index = []
                score = []
                length = len(pSchedule)
                pitch = len(pSchedule[0])
                
                divisions = []
                for div in range(noDivs):
                    row = []
                    row.append(div+1)
                    divEntries = Entry.objects.filter(Q(tournament=self.instance) & Q(division=div+1))
                    divList = list(divEntries)
                    row.append(divList)
                    divisions.append(row)
                divMatches = divMatchesCalc(divisions)

                for entry in pEntries:
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
                            
                            #???
                            if (pDivs > 1) and (pitch == pDivs) and not(pSchedule[j][k] in divMatches[k]):
                                points += 2
                            #???
                
                        if entry in rowCurrent:
                            if entry in rowUpOne:
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
                score.append(float(std))
                score.append(float(mean))
                return score

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
            
            def umpires(schedule, umpires, nPitch):
                arr = createArray(nPitch, len(schedule))                
                count = 0

                for i in range(len(schedule)):
                    for j in range(nPitch):
                
                        users = []
                        for l in range(2):
                            if schedule[i][j] != [0,0]:
                                user = Entry.objects.get(Q(tournament=self.instance) & Q(pk=schedule[i][j][l].id)).user

                            if not(user.groups.filter(name="Admin").exists()):
                                users.append(user)

                        rowCurrent = []
                        for k in range(nPitch):
                            rowCurrent += arr[i][k]

                        temp = 0
                        while len(arr[i][j]) != 2 and temp < 20:
                            match = schedule[i][j]

                            if match == [0,0]:
                                arr[i][j] = [0,0]
                            
                            else:
                                entry = Entry.objects.get(Q(tournament=self.instance) & Q(pk=umpires[count].id))

                                if not(entry in match) and not(entry.umpire in rowCurrent) and not(entry.user in users):
                                    if entry.umpire in arr[i][j]:
                                        arr[i][j].append('Ind.')
                                    else:
                                        arr[i][j].append(entry)
                                
                                if count == (len(umpires)-1):
                                    count = 0
                                else:
                                    count += 1

                            temp += 1
                return arr
            
            #blank knockout round matches
            def final(self, duration):
                print('final')
                
                start = str(Match.objects.filter(tournament=self.id).last().end)
                d = datetime.datetime.strptime(start, '%H:%M:%S')     
                d += datetime.timedelta(minutes=break_duration)
                start = d
                d += datetime.timedelta(minutes=duration)
                end = d

                final = Match(tournament = self,
                                type = 'Final',                  
                                entryOne = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                entryTwo = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                pitch = 1,
                                start = start,
                                end = end,
                                )
                final.save()     

                for i in range(self.noPitches-1):
                    match = Match(tournament = self,
                                    type = 'Free',
                                    entryOne = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                    entryTwo = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                    pitch = i+2,
                                    start = start,
                                    end = end,
                                    )
                    match.save()

            def semis(self, duration):
                print('semis')
                #Semis
                for i in range(3):
                    start = str(Match.objects.filter(tournament=self.id).last().end)
                    d = datetime.datetime.strptime(start, '%H:%M:%S')     
                    d += datetime.timedelta(minutes=break_duration)
                    start = d
                    d += datetime.timedelta(minutes=duration)
                    end = d

                    if i == 2:
                        final = Match(tournament = self,
                                type = 'Final',                  
                                entryOne = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                entryTwo = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                pitch = 1,
                                start = start,
                                end = end,
                                )
                
                        final.save()

                        for i in range(self.noPitches-1):
                            match = Match(tournament = self,
                                            type = 'Free',
                                            entryOne = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                            entryTwo = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                            pitch = i+2,
                                            start = start,
                                            end = end,
                                            )
                            match.save()

                    else:
                        semi = Match(tournament = self,
                                    type = 'Semi-Final',                  
                                    entryOne = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                    entryTwo = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                    pitch = 1,
                                    start = start,
                                    end = end,
                                    )
                        semi.save() 

                        for i in range(self.noPitches-1):
                            match = Match(tournament = self,
                                            type = 'Free',
                                            entryOne = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                            entryTwo = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                            pitch = i+2,
                                            start = start,
                                            end = end,
                                            )
                            match.save()

            def playoffs(self, duration):
                print('Playoffs')
                noDivs = self.noDivisions

                if noDivs == 1:
                    print('One div')
                    types = ['Final',
                            '3rd/4th Playoff',
                            '5th/6th Playoff',
                            '7th/8th Playoff', 
                            '9th/10th Playoff',
                            ]
                    
                    for i in range(math.floor(len(entriesData) / 2)):
                        start = str(Match.objects.filter(tournament=self.id).last().end)
                        d = datetime.datetime.strptime(start, '%H:%M:%S')     
                        d += datetime.timedelta(minutes=break_duration)
                        start = d
                        d += datetime.timedelta(minutes=duration)
                        end = d
                        
                        playoff = Match(tournament = self,
                                    type = types[i],                  
                                    entryOne = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                    entryTwo = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                    pitch = 1,
                                    start = start,
                                    end = end,
                                    )
                        
                        playoff.save()

                        for i in range(self.noPitches-1):
                            match = Match(tournament = self,
                                            type = 'Free',
                                            entryOne = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                            entryTwo = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                            pitch = i+2,
                                            start = start,
                                            end = end,
                                            )
                            match.save()

                elif noDivs == 2:
                    print('Two div')

                    for i in range(4):
                        start = str(Match.objects.filter(tournament=self.id).last().end)
                        d = datetime.datetime.strptime(start, '%H:%M:%S')     
                        d += datetime.timedelta(minutes=break_duration)
                        start = d
                        d += datetime.timedelta(minutes=duration)
                        end = d

                        if i == 2:
                            playoff = Match(tournament = self,
                                        type = '3rd/4th Playoff',                  
                                        entryOne = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                        entryTwo = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                        pitch = 1,
                                        start = start,
                                        end = end,
                                        )   
                            playoff.save() 

                            for i in range(self.noPitches-1):
                                match = Match(tournament = self,
                                                type = 'Free',
                                                entryOne = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                                entryTwo = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                                pitch = i+2,
                                                start = start,
                                                end = end,
                                                )
                                match.save()

                        elif i == 3:
                            final = Match(tournament = self,
                                    type = 'Final',                  
                                    entryOne = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                    entryTwo = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                    pitch = 1,
                                    start = start,
                                    end = end,
                                    )
                    
                            final.save()

                            for i in range(self.noPitches-1):
                                match = Match(tournament = self,
                                                type = 'Free',
                                                entryOne = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                                entryTwo = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                                pitch = i+2,
                                                start = start,
                                                end = end,
                                                )
                                match.save()

                        else:
                            semi = Match(tournament = self,
                                        type = 'Semi-Final',                  
                                        entryOne = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                        entryTwo = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                        pitch = 1,
                                        start = start,
                                        end = end,
                                        )
                            semi.save() 

                            for i in range(self.noPitches-1):
                                match = Match(tournament = self,
                                                type = 'Free',
                                                entryOne = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                                entryTwo = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                                pitch = i+2,
                                                start = start,
                                                end = end,
                                                )
                                match.save()
                    
                    types = ['5th/6th Playoff',
                            '7th/8th Playoff', 
                            '9th/10th Playoff',
                            ]
                    
                    # Getting smaller division
                    divOne = Entry.objects.filter(Q(tournament=self) & Q(division=1)).count()
                    divTwo = Entry.objects.filter(Q(tournament=self) & Q(division=2)).count()

                    if divOne <= divTwo:
                        division = divOne
                    else:
                        division = divTwo

                    #Playoffs
                    for i in range(division-2):

                        start = str(Match.objects.filter(tournament=self.id).last().end)
                        d = datetime.datetime.strptime(start, '%H:%M:%S')     
                        d += datetime.timedelta(minutes=break_duration)
                        start = d
                        d += datetime.timedelta(minutes=duration)
                        end = d
                        
                        playoff = Match(tournament = self,
                                    type = types[i],                  
                                    entryOne = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                    entryTwo = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                    pitch = 1,
                                    start = start,
                                    end = end,
                                    )
                        
                        playoff.save()

                        for i in range(self.noPitches-1):
                            match = Match(tournament = self,
                                            type = 'Free',
                                            entryOne = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                            entryTwo = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                            pitch = i+2,
                                            start = start,
                                            end = end,
                                            )
                            match.save()
                
                elif noDivs == 4:
                    for i in range(8):
                        start = str(Match.objects.filter(tournament=self.id).last().end)
                        d = datetime.datetime.strptime(start, '%H:%M:%S')     
                        d += datetime.timedelta(minutes=break_duration)
                        start = d
                        d += datetime.timedelta(minutes=duration)
                        end = d

                        if i < 4:
                            quarter = Match(tournament = self,
                                        type = 'Quarter-Final',                  
                                        entryOne = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                        entryTwo = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                        pitch = 1,
                                        start = start,
                                        end = end,
                                        )
                            
                            quarter.save()

                            for i in range(self.noPitches-1):
                                match = Match(tournament = self,
                                                type = 'Free',
                                                entryOne = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                                entryTwo = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                                pitch = i+2,
                                                start = start,
                                                end = end,
                                                )
                                match.save()

                        elif i < 6:
                            semi = Match(tournament = self,
                                        type = 'Semi-Final',                  
                                        entryOne = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                        entryTwo = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                        pitch = 1,
                                        start = start,
                                        end = end,
                                        )
                            semi.save() 

                            for i in range(self.noPitches-1):
                                match = Match(tournament = self,
                                                type = 'Free',
                                                entryOne = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                                entryTwo = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                                pitch = i+2,
                                                start = start,
                                                end = end,
                                                )
                                match.save()
                        
                        elif i < 7:
                            final = Match(tournament = self,
                                    type = 'Final',                  
                                    entryOne = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                    entryTwo = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                    pitch = 1,
                                    start = start,
                                    end = end,
                                    )
                    
                            final.save()     
                        
                            for i in range(self.noPitches-1):
                                match = Match(tournament = self,
                                                type = 'Free',
                                                entryOne = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                                entryTwo = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                                pitch = i+2,
                                                start = start,
                                                end = end,
                                                )
                                match.save()

                        else:
                            playoff = Match(tournament = self,
                                        type = '3rd/4th Playoff',                  
                                        entryOne = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                        entryTwo = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                        pitch = 1,
                                        start = start,
                                        end = end,
                                        )   
                            playoff.save() 

                            for i in range(self.noPitches-1):
                                match = Match(tournament = self,
                                                type = 'Free',
                                                entryOne = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                                entryTwo = Entry.objects.get(Q(tournament=self) & Q(pk=entriesData[0][0].id)),
                                                pitch = i+2,
                                                start = start,
                                                end = end,
                                                )
                                match.save()                       
                else:
                    print('invalid')                                                

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
            end = str(self.instance.endTime)
            match_duration = self.instance.matchDuration
            break_duration = self.instance.breakDuration
            halftime_duration = self.instance.halftimeDuration

            #Mapping entries
            entries = Entry.objects.filter(tournament=self.instance)

            for entry in entries:
                row = []
                row.append(entry)
                row.append(entry.division)
                entriesData.append(row)

            while optimum == False and x < (MAX+1):
                
                divisions = []
                matches = []
                array = []
                length = 0
                
                divisions = []
                for div in range(noDivs):
                    row = []
                    row.append(div+1)
                    divEntries = Entry.objects.filter(Q(tournament=self.instance) & Q(division=div+1))
                    divList = list(divEntries)
                    row.append(divList)
                    divisions.append(row)

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
                        efficiency = indexCalc(optimumSchedule, entries, noDivs)
                        scheduled = True
                else:
                    if (x+1) == MAX:
                        optimum = True
                    else:
                        if missing == 0:
                            newEfficiency = indexCalc(OOP, entries, noDivs)
                            if newEfficiency[1] < efficiency[1]:
                                optimumSchedule = OOP
                                efficiency = newEfficiency
                
                x += 1

            if self.instance.umpires == True:
                print("Generating Umpire Schedule")
                while y < 20:
                    umps = []
                    for entry in entries:
                        umps.append(entry)
                    
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
            
            print(efficiency)

            #Timings
            schedLength = len(optimumSchedule)
            tournDuration = (datetime.datetime.strptime(end, '%H:%M:%S') - datetime.datetime.strptime(start, '%H:%M:%S')).total_seconds() / 60

            if self.instance.knockoutRounds == "Playoffs, Semis & Final":
                schedLength += 3
            elif self.instance.knockoutRounds == "Semis & Final":
                schedLength += 2
            elif self.instance.knockoutRounds == "Final":
                schedLength += 1
            else: 
                print('No knockout rounds')

           
            #Ratio set at m:b = 4:1
            if self.instance.matchType == "One Way":
                match_duration = round((4 * int(tournDuration)) / ((5 * schedLength) - 1))
                break_duration = math.floor(match_duration * (1/4))
            else:
                match_duration = round((4 * int(tournDuration)) / ((11 * schedLength) - 2))
                break_duration = math.floor(match_duration * (1/2))
                halftime_duration = math.floor(match_duration * (1/4))

            #Creating Matches
            for i in range(len(optimumSchedule)):
                for j in range(len(optimumSchedule[i])):
                    if not(optimumSchedule[i][j] == [0,0]):
                        if self.instance.matchType == "One Way":
                            duration = match_duration + break_duration
                            if self.instance.umpires == True:
                                match = Match(tournament = self.instance,
                                                division = optimumSchedule[i][j][0].division,                  
                                                entryOne = Entry.objects.get(Q(tournament=self.instance) & Q(pk=optimumSchedule[i][j][0].id)),
                                                entryTwo = Entry.objects.get(Q(tournament=self.instance) & Q(pk=optimumSchedule[i][j][1].id)),
                                                pitch = j+1,
                                                start = datetime.datetime.strptime(start, '%H:%M:%S') + datetime.timedelta(minutes=(duration * i)),
                                                end = datetime.datetime.strptime(start, '%H:%M:%S') + datetime.timedelta(minutes=(match_duration + (duration * i))),
                                                umpireOneName = UmpireSchedule[i][j][0],
                                                umpireTwoName = UmpireSchedule[i][j][1],
                                                )
                                match.save()
                            else:
                                match = Match(tournament = self.instance,
                                                division = optimumSchedule[i][j][0].division,                  
                                                entryOne = Entry.objects.get(Q(tournament=self.instance) & Q(pk=optimumSchedule[i][j][0].id)),
                                                entryTwo = Entry.objects.get(Q(tournament=self.instance) & Q(pk=optimumSchedule[i][j][1].id)),
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
                                            division = optimumSchedule[i][j][0].division,                  
                                            entryOne = Entry.objects.get(Q(tournament=self.instance) & Q(pk=optimumSchedule[i][j][0].id)),
                                            entryTwo = Entry.objects.get(Q(tournament=self.instance) & Q(pk=optimumSchedule[i][j][1].id)),
                                            pitch = j+1,
                                            start = datetime.datetime.strptime(start, '%H:%M:%S') + datetime.timedelta(minutes=(duration * i)),
                                            end = datetime.datetime.strptime(start, '%H:%M:%S') + datetime.timedelta(minutes=(full_match_duration + (duration * i))),
                                            umpireOneName = UmpireSchedule[i][j][0],
                                            umpireTwoName = UmpireSchedule[i][j][1],
                                            )
                                match.save()
                            else:
                                match = Match(tournament = self.instance,
                                            division = optimumSchedule[i][j][0].division,                  
                                            entryOne = Entry.objects.get(Q(tournament=self.instance) & Q(pk=optimumSchedule[i][j][0].id)),
                                            entryTwo = Entry.objects.get(Q(tournament=self.instance) & Q(pk=optimumSchedule[i][j][1].id)),
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
                                            type = 'Free',
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
                                            type = 'Free',
                                            entryOne = Entry.objects.get(Q(tournament=self.instance) & Q(pk=entriesData[0][0].id)),
                                            entryTwo = Entry.objects.get(Q(tournament=self.instance) & Q(pk=entriesData[0][0].id)),
                                            pitch = j+1,
                                            start = datetime.datetime.strptime(start, '%H:%M:%S') + datetime.timedelta(minutes=(duration * i)),
                                            end = datetime.datetime.strptime(start, '%H:%M:%S') + datetime.timedelta(minutes=(full_match_duration + (duration * i))),
                                            )
                            match.save()
                
            #Create blank knockout round matches
            if self.instance.matchType == "One Way":
                duration = match_duration
            else:
                duration = (2 * match_duration) + halftime_duration
            
            if self.instance.knockoutRounds == "Playoffs, Semis & Final":
                playoffs(self.instance, duration)
            elif self.instance.knockoutRounds == "Semis & Final":
                semis(self.instance, duration)
            elif self.instance.knockoutRounds == "Final":
                final(self.instance, duration)    
            else: 
                print('No knockout rounds')
            
            print('generated')
            generated = True
            Tournament.objects.filter(pk=self.instance.id).update(matchDuration=match_duration)
            Tournament.objects.filter(pk=self.instance.id).update(breakDuration=break_duration)
            Tournament.objects.filter(pk=self.instance.id).update(halftimeDuration=halftime_duration)
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