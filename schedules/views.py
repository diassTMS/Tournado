from .forms import SchedulePDFForm, ScheduleForm, LeagueScheduleForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .threads import GenerateScheduleThread, GenerateLeagueScheduleThread
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import UpdateView, DetailView, View
from leagues.models import League, LeagueEntry, LeagueMatch
from django.contrib.auth.decorators import login_required
from tournaments.models import Entry, Match, Tournament
from django.shortcuts import HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, render, redirect
from .models import Schedule, Timings, Rules
from django.http import JsonResponse
from django.contrib import messages
from Tournado import renderers
from django.db.models import Q
import datetime
import time

#TOURNAMENTS

class ScheduleCreateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = Tournament
    form_class = ScheduleForm
    success_url = reverse_lazy('/')
    template_name = "schedule-create.html" 
    
    def form_valid(self, form):        
        GenerateScheduleThread(form.instance).start()
        return super().form_valid(form)
    
    def get_success_url(self):
        tourn = self.object.id
        sched = Schedule.objects.get(tournament__id=tourn)
        return reverse_lazy('schedule-pdf', kwargs={'pk': sched.id})

    def get_context_data(self,*args, **kwargs):
        context = super(ScheduleCreateView, self).get_context_data(*args,**kwargs)
        context['entries'] = Entry.objects.filter(tournament=self.object.id)
        context['tournament'] = self.object
        return context
    
    def test_func(self):
        entry = self.get_object()
        if self.request.user == entry.user:
            return True
        return False
    
def publish_schedule(request, pk):
    sched = get_object_or_404(Schedule, id=pk)
    if sched.published == True:
        sched.published = False
        sched.save()
        messages.success(request, 'Schedule unpublished!')
    else:
        sched.published = True
        sched.save()
        messages.success(request, 'Schedule published!')
    
    return redirect(reverse_lazy('user-tourn-detail',  kwargs={'pk': sched.tournament.id}))

class SchedulePDFView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = Schedule
    form_class = SchedulePDFForm
    success_message = 'Your pdf is currently being generated!'       
    template_name = "schedule-pdf.html" 
    
    def form_valid(self, form):        
        #GenerateScheduleThread(form.instance).start()
        sched_id = form.instance.id
        form.save()

        return HttpResponseRedirect(reverse('schedule-pdf', kwargs={'pk': sched_id}))

    def get_context_data(self,*args, **kwargs):
        context = super(SchedulePDFView, self).get_context_data(*args,**kwargs)
        sched = Schedule.objects.get(pk=self.object.pk)
        context['tourn'] = sched.tournament
        return context
    
    def test_func(self):
        entry = self.get_object()
        if self.request.user == entry.tournament.user:
            return True
        return False
    
class PDFView(View):    
    def get(self, request, pk):
        tournament = Tournament.objects.get(pk=pk)
        schedule = []
        start = Match.objects.filter(Q(tournament=tournament.id)).values('start').distinct().order_by('start')
        length = start.count()

        for i in range(length):
            qs = Match.objects.filter(Q(tournament=tournament.id) & Q(start=start[i].get('start'))).order_by('pitch')
            row = []

            row.append(qs.first())
            freeCount = 0
            for j in range(len(qs)):
                row.append(qs[j])
                if qs[j].type == 'Free':
                    freeCount += 1

            while len(row) < (tournament.noPitches + 1):
                row.append("blank")

            if freeCount != tournament.noPitches:
                schedule.append(row)

        title = tournament.name
        sched = Schedule.objects.get(tournament=tournament)
        timings = Timings.objects.filter(schedule=sched)
        rules = Rules.objects.filter(schedule=sched)
        timed = sched.timed

        data = {
            'tournament': Tournament.objects.get(pk=pk), 
            'title': title,
            'schedule': schedule,
            'timings': timings,
            'rules': rules,
            'timed': timed,
            'range': range(tournament.noPitches),
        }
        
        return renderers.render_to_pdf('pdf.html', data)

class UmpirePDFView(View):    
    def get(self, request, pk):
        tournament = Tournament.objects.get(pk=pk)
        schedule = []
        start = Match.objects.filter(Q(tournament=tournament.id) & ~Q(division=0)).values('start').distinct().order_by('start')
        length = start.count()

        for i in range(length):
            qs = Match.objects.filter(Q(tournament=tournament.id) & Q(start=start[i].get('start')) & ~Q(division=0)).order_by('pitch')
            row = []

            row.append(qs.first())
            for j in range(len(qs)):
                row.append(qs[j])

            
            while len(row) < (tournament.noPitches + 1):
                row.append('blank')

            schedule.append(row)

        title = tournament.name
        sched = Schedule.objects.get(tournament=tournament)
        timings = Timings.objects.filter(schedule=sched)
        rules = Rules.objects.filter(schedule=sched)
        timed = sched.timed

        data = {
            'tournament': Tournament.objects.get(pk=pk), 
            'title': title,
            'schedule': schedule,
            'timings': timings,
            'rules': rules,
            'timed': timed,
            'range': range(tournament.noPitches),
        }
        
        return renderers.render_to_pdf('umpire-pdf.html', data)

#LEAGUES

class LeagueScheduleCreateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = League
    form_class = LeagueScheduleForm
    success_url = reverse_lazy('/')
    success_message = 'Your matches have been successfully generated!'       
    template_name = "leagues/schedule-create.html" 
    
    def form_valid(self, form):        
        GenerateLeagueScheduleThread(form.instance).start()
        return super().form_valid(form)
    
    def get_success_url(self):
        time.sleep(4)
        league = self.object.id
        return reverse_lazy('user-league-detail', kwargs={'pk': league})

    def get_context_data(self,*args, **kwargs):
        context = super(LeagueScheduleCreateView, self).get_context_data(*args,**kwargs)
        context['entries'] = LeagueEntry.objects.filter(league=self.object.id)
        context['league'] = self.object
        return context
    
    def test_func(self):
        entry = self.get_object()
        if self.request.user == entry.user:
            return True
        return False
    
class DragDropView(DetailView):
    model = Tournament
    template_name = 'drag-drop.html'
    
    def get_context_data(self,*args, **kwargs):
        context = super(DragDropView, self).get_context_data(*args,**kwargs)
        schedule = []
        start = Match.objects.filter(Q(tournament=self.object.id)).values('start').distinct().order_by('start')
        length = start.count()

        for i in range(length):
            qs = Match.objects.filter(Q(tournament=self.object.id) & Q(start=start[i].get('start'))).order_by('pitch')
            row = []

            row.append(qs.first())
            freeCount = 0
            for j in range(len(qs)):
                row.append(qs[j])
                if qs[j].type == 'Free':
                    freeCount += 1

            while len(row) < (self.object.noPitches + 1):
                row.append("blank")

            if freeCount != self.object.noPitches:
                print('freerow')
           
            schedule.append(row)
                
        context['schedule'] = schedule
        context['range'] = range(self.object.noPitches)
        context['tourn'] = self.object
        return context
    
class ChangeSheetAssign(LoginRequiredMixin, View):

    @staticmethod
    def get(request, *args, **kwargs):
        matchOne_Id = kwargs['matchOne_id']
        matchTwo_Id = kwargs['matchTwo_id']

        matchOne = Match.objects.get(pk=matchOne_Id)
        matchTwo = Match.objects.get(pk=matchTwo_Id)

        matchOnePitch = matchOne.pitch
        matchOneStart = matchOne.start
        matchOneEnd = matchOne.end
        matchTwoPitch = matchTwo.pitch
        matchTwoStart = matchTwo.start
        matchTwoEnd = matchTwo.end

        matchOne.pitch = matchTwoPitch
        matchOne.start = matchTwoStart
        matchOne.end = matchTwoEnd
        matchTwo.pitch = matchOnePitch
        matchTwo.start = matchOneStart
        matchTwo.end = matchOneEnd

        matchOne.save()
        matchTwo.save()

        print('updated')

        return redirect(reverse_lazy('drag-drop', kwargs={'pk': matchOne.tournament.id}))