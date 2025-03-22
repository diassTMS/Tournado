from typing import Any
from django.db.models.query import QuerySet
from .tables import ScoreTable, LargeKnockoutTable, SmallKnockoutTable, LeagueScoreTable, FinalRankTable
from django.contrib.messages.views import SuccessMessageMixin
from leagues.models import League, LeagueEntry, LeagueMatch
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User, Group
from tournaments.models import Tournament, Entry
from .filters import TournFilter, LeagueFilter, UserFilter
from django.shortcuts import render, redirect
from django_filters.views import FilterView
from django_tables2 import MultiTableMixin
from django.urls import reverse_lazy
from django.template.loader import render_to_string
from django.http import JsonResponse
from tournaments.models import Match
from django.contrib import messages
from django.db.models import F, Q
from leagues.models import League
from .forms import UserCreateForm
import datetime
from django.views.generic import (TemplateView,
                                  DetailView,
                                  ListView,
                                  CreateView,
                                  )


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournaments'] = Tournament.objects.filter(date__gte=datetime.date.today()).order_by('date')[:3]
        context['leagues'] = League.objects.filter(endDate__gte=datetime.date.today(), startDate__lte=datetime.date.today())[:2]
        return context
    
class UserCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = "user-create.html"
    success_url = ''
    success_message = "User created successfully!"
    
    def get_success_url(self):
        return reverse_lazy('user-list')
    

@login_required
def AccountView(request):
    numT = Tournament.objects.filter(user=request.user).count()
    numE = Entry.objects.filter(user=request.user).count()
    numL = League.objects.filter(user=request.user).count()
    group = Group.objects.get(name=request.user.groups.first()).id

    context = {
        'numTourns': numT,
        'numEntries': numE,
        'numLeagues': numL,
        'user': request.user,
        'school': 1,
        'club': 2,
        'group': group,
    }

    return render(request, 'account.html', context)

class TournFilterView(FilterView):
    model = Tournament
    queryset = Tournament.objects.filter(date__gte=datetime.date.today()).order_by('date')
    template_name = 'tourn-list.html'
    filterset_class = TournFilter
    context_object_name = 'tournaments'

class LeagueFilterView(FilterView):
    model = League
    queryset = League.objects.filter(endDate__gte=datetime.date.today(), startDate__lte=datetime.date.today())
    template_name = 'leagues/league-list.html'
    filterset_class = LeagueFilter
    context_object_name = 'leagues'

class UserFilterView(FilterView):
    model = User
    queryset = User.objects.all().exclude(groups__name="Admin")
    template_name = 'user-list.html'
    filterset_class = UserFilter
    context_object_name = 'users'

    def get_queryset(self):
        if self.request.user.is_superuser:
            return User.objects.all()
        else:
            return User.objects.all().exclude(groups__name="Admin")

class LiveScoreView(MultiTableMixin, TemplateView):
    model = Entry
    template_name = 'score-table.html'
    table_prefix = 'Division_{}'
    tables = []
    
    def get_context_data(self,*args, **kwargs):
        context = super(LiveScoreView, self).get_context_data(*args,**kwargs)
        tables = []
        tournament = Tournament.objects.get(pk=kwargs['pk'])
        noDivs = tournament.noDivisions

        for i in range(noDivs):
            qs = Entry.objects.filter(Q(tournament=tournament.id) & Q(division=(i+1))).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
            tables.append(ScoreTable(qs))

        noPlayedMatches = Match.objects.filter(Q(tournament=tournament.id) & Q(played=True)).count()
        matches = Match.objects.filter(Q(tournament=tournament.id) & ~Q(division=0))
        matchCount = 0
        for match in matches:
            if not(match.entryOne == match.entryTwo):
                matchCount += 1

        if (noPlayedMatches >= matchCount) and (matches != 0):
            final = Match.objects.filter(Q(tournament=tournament.id) & Q(division=0) & Q(type="Final"))
            semis = Match.objects.filter(Q(tournament=tournament.id) & Q(division=0) & Q(type="Semi-Final"))
            threeFour = Match.objects.filter(Q(tournament=tournament.id) & Q(division=0) & Q(type="3rd/4th Playoff"))
            playoffs = Match.objects.filter(Q(tournament=tournament.id) & Q(division=0) & ~Q(type="Free") & ~Q(type="Semi-Final") & ~Q(type="Final"))
            qs = final.union(semis).union(threeFour).union(playoffs)

            for match in qs:
                if match.entryOne == match.entryTwo:
                    qs = qs.exclude(id=match.id)

            LKnockoutTable = LargeKnockoutTable(qs)
            SKnockoutTable = SmallKnockoutTable(qs)
        else:
            LKnockoutTable = []
            SKnockoutTable = []

        if tournament.finished == True:
            if tournament.knockoutRounds != "None":
                final =  Match.objects.get(Q(tournament=tournament.id) & Q(type="Final"))
                if final.goalsOne > final.goalsTwo:
                    winner = final.entryOne
                    runnerUp = final.entryTwo

                elif final.goalsOne < final.goalsTwo:
                    winner = final.entryTwo    
                    runnerUp = final.entryOne                                                        

                else:
                    if final.pfOne > final.pfTwo:
                        winner = final.entryOne
                        runnerUp = final.entryTwo
                    else:
                        winner = final.entryTwo 
                        runnerUp = final.entryOne

                ranks = Entry.objects.filter(tournament=tournament.id).exclude(rank=0).order_by('rank')
                noRank = Entry.objects.filter(tournament=tournament.id, rank=0).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())

                count = ranks.count() + 1
                for entry in noRank:
                    entry.rank = count 
                    entry.save()
                    count += 1

                ranksQs = Entry.objects.filter(tournament=tournament.id).order_by('rank')
                rankingTable = FinalRankTable(ranksQs)
                
            else:
                if tournament.noDivisions == 1:
                    ranksQs = Entry.objects.filter(tournament=tournament.id).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
                    winner = ranksQs[0]
                    runnerUp = ranksQs[1]

                    count = 1
                    for entry in ranksQs:
                        entry.rank = count
                        entry.save()
                        count += 1
                        
                    rankingTable = FinalRankTable(ranksQs)

                else:
                    winner = None
                    runnerUp = None
                    rankingTable = []

        else:
            winner = None
            runnerUp = None
            rankingTable = []


        currentTime = datetime.datetime.now().time() 
        #Complicated query!: Match in tourn amd either (match timings are current time) or (current is true) whilst excluding matches shere finished is true
        currentMatches = Match.objects.filter(Q(tournament=tournament.id) & Q(Q(start__lte=F('end')), Q(start__lte=currentTime), end__gte=currentTime) | Q(current=True)).exclude(played=True)

        context['tables'] = tables
        context['LKnockoutTable'] = LKnockoutTable
        context['SKnockoutTable'] = SKnockoutTable
        context['rankingTable'] = rankingTable
        context['winner'] = winner
        context['runnerUp'] = runnerUp
        context['current'] = currentMatches
        context['tournament'] = Tournament.objects.get(pk=kwargs['pk'])
        context['title'] = "Live"
        
        return context
    
#LEAGUE SCORE TABLE

class LeagueCurrentScoreView(MultiTableMixin, TemplateView):
    model = LeagueEntry
    template_name = 'leagues/score-table.html'
    tables = []
    
    def get_context_data(self,*args, **kwargs):
        context = super(LeagueCurrentScoreView, self).get_context_data(*args,**kwargs)
        tables = []
        league = League.objects.get(pk=kwargs['pk'])

        qs = LeagueEntry.objects.filter(league=league.id).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
        table = LeagueScoreTable(qs)

        if league.finished == True:
            ranks = LeagueEntry.objects.filter(league=league.id).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
            winner = ranks[0]
            runnerUp = ranks[1]
        else:
            winner = None
            runnerUp = None

        context['table'] = table
        context['winner'] = winner
        context['runnerUp'] = runnerUp
        context['league'] = League.objects.get(pk=kwargs['pk'])
        context['title'] = "Current"
        
        return context
    
#TOURN
class EntryStatsView(DetailView):
    model = Entry
    template_name = "entry-stats.html"

    def get_context_data(self, **kwargs):
        context = super(EntryStatsView, self).get_context_data(**kwargs)
        currentTime = datetime.datetime.now().time()
        context['max_played'] = Entry.objects.filter(Q(tournament=self.object.tournament.id) & Q(division=self.object.division)).count() - 1
        context['matches'] = Match.objects.filter(Q(entryOne=self.object.id) | Q(entryTwo=self.object.id)).order_by('start')
        context['current'] =  Match.objects.filter(Q(tournament=self.object.tournament.id) & Q(Q(start__lte=F('end')), Q(start__lte=currentTime), end__gte=currentTime) | Q(current=True))
        context['league'] = False
        return context

#LEAGUE
class LeagueEntryStatsView(DetailView):
    model = LeagueEntry
    template_name = "entry-stats.html"

    def get_context_data(self, **kwargs):
        context = super(LeagueEntryStatsView, self).get_context_data(**kwargs)
        current = datetime.datetime.today().date()
        context['max_played'] = LeagueEntry.objects.filter(league=self.object.league.id).count() - 1
        context['matches'] = LeagueMatch.objects.filter(Q(entryOne=self.object.id) | Q(entryTwo=self.object.id)).order_by('start')
        context['current'] =  LeagueMatch.objects.filter(Q(league=self.object.league.id) & Q(date=current))
        context['league'] = True
        return context
    
def search_bar(request):
    if request.method == 'GET':
        search_query = request.GET.get('data', None)
        if search_query == "":
            qs = Tournament.objects.filter(name__icontains = search_query, date__lt=datetime.datetime.today().date()).order_by('-date')[:2]
        elif search_query == "All" or search_query == "all":
            qs = Tournament.objects.filter(date__lt=datetime.datetime.today().date()).order_by('-date')
        else:
            qs = Tournament.objects.filter(Q(name__icontains = search_query) | Q(date__icontains = search_query) | Q(group__icontains = search_query) | Q(level__icontains = search_query) | Q(gender__icontains = search_query) | Q(age__icontains = search_query), date__lt=datetime.datetime.today().date()).order_by('-date')
        data = dict()
        data['result'] = render_to_string(template_name='include/past-tourns.html',
                                        request=request,
                                        context={'tournaments': qs,
                                                }
                                        )
        return JsonResponse(data)
    
def search_bar_leagues(request):
    if request.method == 'GET':
        search_query = request.GET.get('data', None)
        if search_query == "":
            qs = League.objects.filter(name__icontains = search_query, date__lt=datetime.datetime.today().date()).order_by('-date')[:2]
        elif search_query == "All" or search_query == "all":
            qs = League.objects.filter(date__lt=datetime.datetime.today().date()).order_by('-date')
        else:
            qs = League.objects.filter(Q(name__icontains = search_query) | Q(group__icontains = search_query) | Q(level__icontains = search_query) | Q(gender__icontains = search_query) | Q(age__icontains = search_query), endDate__lt=datetime.date.today()).order_by('-endDate')
        data = dict()
        data['result'] = render_to_string(template_name='include/past-leagues.html',
                                        request=request,
                                        context={'leagues': qs,
                                                }
                                        )
        return JsonResponse(data)

class LiveEventView(ListView):
    template_name = 'live-events.html'
    context_object_name = 'tournaments'
    model = Tournament

    def get_context_data(self, **kwargs):
        context = super(LiveEventView, self).get_context_data(**kwargs)
        context.update({
            'leagues': League.objects.filter(endDate__gte=datetime.date.today(), startDate__lte=datetime.date.today()),
        })
        return context

    def get_queryset(self):
        return Tournament.objects.filter(date=datetime.datetime.today().date()).order_by('startTime')

class PastEventView(ListView):
    template_name = 'past-events.html'
    context_object_name = 'tournaments'
    model = Tournament

    def get_context_data(self, **kwargs):
        context = super(PastEventView, self).get_context_data(**kwargs)
        context.update({
            'leagues': League.objects.filter(endDate__lt=datetime.date.today()),
        })
        return context

    def get_queryset(self):
        return Tournament.objects.filter(date__lt=datetime.datetime.today().date()).order_by('-date')[:2]


class PastScoreView(MultiTableMixin, TemplateView):
    model = Entry
    template_name = 'score-table.html'
    table_prefix = 'Division_{}'
    tables = []
    
    def get_context_data(self,*args, **kwargs):
        context = super(PastScoreView, self).get_context_data(*args,**kwargs)
        tables = []
        tournament = Tournament.objects.get(pk=kwargs['pk'])

        noDivs = tournament.noDivisions
        for i in range(noDivs):
            qs = Entry.objects.filter(Q(tournament=tournament.id) & Q(division=(i+1))).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
            tables.append(ScoreTable(qs))

        noPlayedMatches = Match.objects.filter(Q(tournament=tournament.id) & Q(played=True)).count()
        matches = Match.objects.filter(Q(tournament=tournament.id) & ~Q(division=0))
        matchCount = 0
        for match in matches:
            if not(match.entryOne == match.entryTwo):
                matchCount += 1

        if (noPlayedMatches >= matchCount) and (matches != 0):
            final = Match.objects.filter(Q(tournament=tournament.id) & Q(division=0) & Q(type="Final"))
            semis = Match.objects.filter(Q(tournament=tournament.id) & Q(division=0) & Q(type="Semi-Final"))
            threeFour = Match.objects.filter(Q(tournament=tournament.id) & Q(division=0) & Q(type="3rd/4th Playoff"))
            playoffs = Match.objects.filter(Q(tournament=tournament.id) & Q(division=0) & ~Q(type="Semi-Final") & ~Q(type="Final"))
            qs = final.union(semis).union(threeFour).union(playoffs)

            LKnockoutTable = LargeKnockoutTable(qs)
            SKnockoutTable = SmallKnockoutTable(qs)
        else:
            LKnockoutTable = []
            SKnockoutTable = []

        if tournament.finished == True:
            if tournament.knockoutRounds != "None":
                final =  Match.objects.get(Q(tournament=tournament.id) & Q(type="Final"))
                if final.goalsOne > final.goalsTwo:
                    winner = final.entryOne
                    runnerUp = final.entryTwo

                elif final.goalsOne < final.goalsTwo:
                    winner = final.entryTwo    
                    runnerUp = final.entryOne                                                        

                else:
                    if final.pfOne > final.pfTwo:
                        winner = final.entryOne
                        runnerUp = final.entryTwo
                    else:
                        winner = final.entryTwo 
                        runnerUp = final.entryOne

                ranksQs = Entry.objects.filter(tournament=tournament.id).order_by('rank')
                rankingTable = FinalRankTable(ranksQs)

            else:
                if tournament.noDivisions == 1:
                    ranks = Entry.objects.filter(tournament=tournament.id).order_by(F('points').desc(), F('goalDiff').desc(), F('forGoals').desc())
                    winner = ranks[0]
                    runnerUp = ranks[1] 
                    rankingTable = FinalRankTable(ranks)
 
                else:
                    winner = None
                    runnerUp = None
                    rankingTable = []
        else:
            winner = None
            runnerUp = None
            rankingTable = []

        currentMatches = []

        context['tables'] = tables
        context['LKnockoutTable'] = LKnockoutTable
        context['SKnockoutTable'] = SKnockoutTable
        context['rankingTable'] = rankingTable
        context['winner'] = winner
        context['runnerUp'] = runnerUp
        context['current'] = currentMatches
        context['tournament'] = Tournament.objects.get(pk=kwargs['pk'])
        context['title'] = "Past"
        
        return context

class UserListView(ListView):
    template_name = 'user-list.html'
    context_object_name = 'users'
    model = User

    def get_queryset(self):
        return User.objects.all()
