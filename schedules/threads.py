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
            umpireSchedules = []
            divSchedules = []
            playoffSched = []
            y = 0
            stanDev = 99

#--------------------------------------------------------------------------------------------------
#Sub Programs
#--------------------------------------------------------------------------------------------------

            def indexCalc(pSchedule, pEntries, pDivs, pTourn):
                divMatches = []
                index = []
                score = []
                length = len(pSchedule)
                pitch = len(pSchedule[0])
                
                divisions = []
                for div in range(noDivs):
                    row = []
                    row.append(div+1)
                    divEntries = Entry.objects.filter(Q(tournament=pTourn) & Q(division=div+1))
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
            
            def optimumSchedule(pDivEntries, pPitches, pDivs, pEntries, pTourn):
                pOptSched = []
                efficiency = []
                optimum = False
                scheduled = False
                x = 0
                increase = 0
                max = 100
                 
                while optimum == False and x < (max+1):
                
                    divisions = []
                    matches = []
                    array = []
                    length = 0
                    
                    divisions = []
                    for div in range(pDivs):
                        row = []
                        row.append(div+1)
                        divList = list(pDivEntries[div])
                        row.append(divList)
                        divisions.append(row)

                    matches = matchesCalc(divisions)
                    
                    if x == max:
                        increase += 1
                        x = 0
                    
                    length = math.ceil(len(matches) / pPitches) + increase
                    
                    if x > 0:
                        random.shuffle(matches)
                        
                    array = createArray(pPitches, length)
                    OOP, missing = schedule(length, pPitches, array, matches)
                    
                    if scheduled == False:
                        if missing == 0:
                            pOptSched = OOP
                            efficiency = indexCalc(pOptSched, pEntries, pDivs, pTourn)
                            scheduled = True
                    else:
                        if (x+1) == max:
                            optimum = True
                        else:
                            if missing == 0:
                                newEfficiency = indexCalc(OOP, pEntries, pDivs, pTourn)
                                if newEfficiency[1] < efficiency[1]:
                                    pOptSched = OOP
                                    efficiency = newEfficiency
                    
                    x += 1

                return pOptSched
            
            def umpires(pSchedule, pEntries, pPitch, pTourn, pEntriesData):
                y = 0
                stanDev = 99

                while y < 20:
                    umps = []
                    for entry in pEntries:
                        umps.append(entry)
                    
                    random.shuffle(umps)
                    arr = createArray(pPitch, len(pSchedule))                
                    count = 0

                    for i in range(len(pSchedule)):
                        for j in range(pPitch):
                    
                            users = []
                            for l in range(2):
                                if pSchedule[i][j] != [0,0]:
                                    user = Entry.objects.get(Q(tournament=pTourn) & Q(pk=pSchedule[i][j][l].id)).user

                                if not(user.groups.filter(name="Admin").exists()):
                                    users.append(user)

                            rowCurrent = []
                            for k in range(pPitch):
                                rowCurrent += arr[i][k]

                            temp = 0
                            while len(arr[i][j]) != 2 and temp < 20:
                                match = pSchedule[i][j]

                                if match == [0,0]:
                                    arr[i][j] = [0,0]
                                
                                else:
                                    entry = Entry.objects.get(Q(tournament=pTourn) & Q(pk=umps[count].id))

                                    if not(entry in match) and not(entry.umpire in rowCurrent) and not(entry.user in users):
                                        if entry.umpire in arr[i][j]:
                                            arr[i][j].append('Ind.')
                                        else:
                                            arr[i][j].append(entry)
                                    
                                    if count == (len(umps)-1):
                                        count = 0
                                    else:
                                        count += 1

                                temp += 1
                        
                    num = []
                    for j in range(len(pEntries)):
                        count = 0
                        umpire = Entry.objects.get(Q(tournament=pTourn) & Q(pk=pEntriesData[j][0].id)).umpire
                        for k in range(len(arr)):
                            for l in range(len(arr[k])):
                                if umpire in arr[k][l]:
                                    count += 1
                        
                        num.append(count)

                    if np.std(num) < stanDev:
                        stanDev = np.std(num)
                        umpireSchedule = arr
                    
                    y += 1
                
                return umpireSchedule
            
            def timings(pTourn, pArr, pStart, pEnd, pAddLength):
                pSchedLength = len(pArr) + pAddLength
                tournDuration = (datetime.datetime.strptime(pEnd, '%H:%M:%S') - datetime.datetime.strptime(pStart, '%H:%M:%S')).total_seconds() / 60
                match_duration = 0
                break_duration = 0
                halftime_duration = 0

                #Ratio set at m:b = 4:1
                if pTourn.matchType == "One Way":
                    match_duration = round((4 * int(tournDuration)) / ((5 * pSchedLength) - 1))
                    break_duration = math.floor(match_duration * (1/4))
                    duration = match_duration + break_duration

                else:
                    match_duration = round((4 * int(tournDuration)) / ((11 * pSchedLength) - 2))
                    break_duration = math.floor(match_duration * (1/2))
                    halftime_duration = math.floor(match_duration * (1/4))
                    duration = (2 * match_duration) + halftime_duration + break_duration

                Tournament.objects.filter(pk=self.instance.id).update(matchDuration=match_duration)
                Tournament.objects.filter(pk=self.instance.id).update(breakDuration=break_duration)
                Tournament.objects.filter(pk=self.instance.id).update(halftimeDuration=halftime_duration)

                return match_duration, break_duration, duration
            
            def createMatches(pTourn, pArr, pUmpArr, pStart, pDuration, pMatch):
                for i in range(len(pArr)):
                    for j in range(len(pArr[i])):

                        #Free Matches
                        if pArr[i][j] == [0,0]:
                            match = Match(tournament = pTourn,
                                        type = 'Free',
                                        entryOne = Entry.objects.filter(tournament=pTourn).first(),
                                        entryTwo = Entry.objects.filter(tournament=pTourn).first(),
                                        pitch = j+1,
                                        start = datetime.datetime.strptime(pStart, '%H:%M:%S') + datetime.timedelta(minutes=(pDuration * i)),
                                        end = datetime.datetime.strptime(pStart, '%H:%M:%S') + datetime.timedelta(minutes=(pMatch + (pDuration * i))),
                                        )
                            match.save()
                        
                        #Playoff Matches
                        elif len(pArr[i][j]) > 2:
                            match = Match(tournament = pTourn,
                                        type = pArr[i][j],
                                        entryOne = Entry.objects.filter(tournament=pTourn).first(),
                                        entryTwo = Entry.objects.filter(tournament=pTourn).first(),
                                        pitch = j+1,
                                        start = datetime.datetime.strptime(pStart, '%H:%M:%S') + datetime.timedelta(minutes=(pDuration * i)),
                                        end = datetime.datetime.strptime(pStart, '%H:%M:%S') + datetime.timedelta(minutes=(pMatch + (pDuration * i))),
                                        )
                            match.save()

                        #Division Matches
                        else:
                            if pTourn.umpires == True:
                                match = Match(tournament = pTourn,
                                                division = pArr[i][j][0].division,                  
                                                entryOne = Entry.objects.get(Q(tournament=pTourn) & Q(pk=pArr[i][j][0].id)),
                                                entryTwo = Entry.objects.get(Q(tournament=pTourn) & Q(pk=pArr[i][j][1].id)),
                                                pitch = j+1,
                                                start = datetime.datetime.strptime(pStart, '%H:%M:%S') + datetime.timedelta(minutes=(pDuration * i)),
                                                end = datetime.datetime.strptime(pStart, '%H:%M:%S') + datetime.timedelta(minutes=(pMatch + (pDuration * i))),
                                                umpireOneName = pUmpArr[i][j][0],
                                                umpireTwoName = pUmpArr[i][j][1],
                                                )
                                match.save()

                            else:
                                match = Match(tournament = pTourn,
                                                division = pArr[i][j][0].division,                  
                                                entryOne = Entry.objects.get(Q(tournament=pTourn) & Q(pk=pArr[i][j][0].id)),
                                                entryTwo = Entry.objects.get(Q(tournament=pTourn) & Q(pk=pArr[i][j][1].id)),
                                                pitch = j+1,
                                                start = datetime.datetime.strptime(pStart, '%H:%M:%S') + datetime.timedelta(minutes=(pDuration * i)),
                                                end = datetime.datetime.strptime(pStart, '%H:%M:%S') + datetime.timedelta(minutes=(pMatch + (pDuration * i))),
                                                )
                                match.save()

            def knockouts(pTourn):
                addLength = 0
                noPitch = pTourn.noPitches
                pArr = []

                #Calculating how many rows to add onto schedule to account for playoffs
                if pTourn.knockoutRounds == "Playoffs, Semis & Final":
                    if pTourn.noDivisions == 1:
                        noMatch = math.floor(pTourn.noTeams / 2)
                        types = ['Final',
                                '3rd/4th Playoff',
                                '5th/6th Playoff',
                                '7th/8th Playoff', 
                                '9th/10th Playoff',
                                ]
                                
                        pArr = np.array(types)
                        pArr.resize(math.ceil(noMatch / noPitch), noPitch)
                        pArr[np.isin(pArr, '')] = 'Free'                   
                    
                    elif pTourn.noDivisions == 2:
                        pArr = createArray(noPitch, math.ceil((math.floor(pTourn.noTeams / 2) / noPitch) + (2 / noPitch)))

                        if noPitch > 1:
                            pArr[0][0] = pArr[0][1]= "Semi-Final"
                            pArr[1][0] = "Final"
                            pArr[1][1] = "3rd/4th Playoff"

                            if pTourn.noTeams < 6:
                                types = []
                            elif pTourn.noTeams < 8:
                                types = ['5th/6th Playoff',]
                            elif pTourn.noTeams < 10:
                                types = ['5th/6th Playoff',
                                        '7th/8th Playoff',
                                        ]
                            else:
                                types = ['5th/6th Playoff',
                                        '7th/8th Playoff', 
                                        '9th/10th Playoff', 
                                        ]

                            for i in range(len(pArr)):
                                for j in range(len(pArr[i])):
                                    if pArr[i][j] == []:
                                        if len(types) != 0:
                                            pArr[i][j] = types[0]
                                            del types[0]
                                        else:
                                            pArr[i][j] = [0,0]
                        
                        else:
                            types = ['Semi-Final',
                                    'Semi-Final',
                                    'Final',
                                    '3rd/4th Playoff',
                                    '5th/6th Playoff',
                                    '7th/8th Playoff', 
                                    '9th/10th Playoff',
                                    ]
                            
                            pArr = np.array(types)
                            pArr.resize(math.ceil(7 / noPitch), noPitch)
                            pArr[np.isin(pArr, '')] = 'Free'

                    else:
                        types = [['Quarter-Final', 'Quarter-Final', 'Quarter-Final', 'Quarter-Final'],
                                ['Semi-Final', 'Semi-Final'],
                                ['Final', '3rd/4th Playoff']
                                ]
                        
                        pArrOne = np.array(types[0])
                        pArrOne.resize(math.ceil(4 / noPitch), noPitch)

                        pArrTwo = np.array(types[1])
                        pArrTwo.resize(math.ceil(2 / noPitch), noPitch)
                        
                        pArrThree = np.array(types[2])
                        pArrThree.resize(math.ceil(2 / noPitch), noPitch)

                        pArr = np.concatenate((pArrOne, pArrTwo, pArrThree))
                        pArr[np.isin(pArr, '')] = 'Free'

                elif pTourn.knockoutRounds == "Semis & Final":
                    types = [['Semi-Final', 'Semi-Final'],
                            ['Final']]
                        
                    pArrOne = np.array(types[0])
                    pArrOne.resize(math.ceil(2 / noPitch), noPitch)

                    pArrTwo = np.array(types[1])
                    pArrTwo.resize(math.ceil(1 / noPitch), noPitch)

                    pArr = np.concatenate((pArrOne, pArrTwo))
                    pArr[np.isin(pArr, '')] = 'Free'

                elif pTourn.knockoutRounds == "Final":
                    pArr = np.array(['Final'])
                    pArr.resize(1, noPitch)
                    pArr[np.isin(pArr, '')] = 'Free'
                
                else: 
                    print('No knockout rounds')

                addLength = len(pArr)

                return addLength, pArr

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

            #Mapping entries (Kinda pointless?)
            entries = Entry.objects.filter(tournament=self.instance)

            for entry in entries:
                row = []
                row.append(entry)
                row.append(entry.division)
                entriesData.append(row)
            
            divEntries = []
            for i in range(noDivs):
                divEntry = Entry.objects.filter(Q(tournament=self.instance) & Q(division=i+1))
                divEntries.append(divEntry)

            #Calculating optimum schedule
            optSched = optimumSchedule(divEntries, noPitches, noDivs, entries, self.instance)

            #Generating umpire schedule if necessary
            if self.instance.umpires == True:
                #At some point change subprogram cuz it's a bit shit!
                umpSched = umpires(optSched, entries, noPitches, self.instance, entriesData)
            
            #Generating playoff schedule
            schedLength, playoffSched = knockouts(self.instance)

            #Timings
            start = str(self.instance.startTime)
            end = str(self.instance.endTime)           
            matchDur, breakDur, duration = timings(self.instance, optSched, start, end, schedLength)

            #Creating div matches        
            createMatches(self.instance, optSched, umpSched, start, duration, matchDur)

            #Creating playoff matches
            playoffStart = datetime.datetime.strptime(str(Match.objects.filter(tournament=self.instance.id).last().end), '%H:%M:%S') + datetime.timedelta(minutes=breakDur)
            playoffStart = str(playoffStart.strftime('%H:%M:%S'))
            createMatches(self.instance, playoffSched, umpSched, playoffStart, duration, matchDur)
            
            print('generated')
            Tournament.objects.filter(pk=self.instance.id).update(generatedSchedule=True)

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