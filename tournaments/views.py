from .forms import TournForm, EntryForm, EntryUpdateForm, MatchKnockoutUpdateForm, ResultForm, SignupForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, get_object_or_404, redirect, HttpResponseRedirect
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.decorators import login_required
from .filters import TournUserFilter, EntryUserFilter
from django.contrib.auth.models import User, Group
from django.urls import reverse_lazy, reverse
from .models import Tournament, Entry, Match
from django_filters.views import FilterView
from orders.models import Order, OrderItem
from .threads import EntryUpdateThread
from django.core.mail import send_mail
from django.contrib.auth import logout
from schedules.models import Schedule
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from users.models import Profile
from django.db.models import Q
from Tournado import settings
import datetime
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.views.generic import (DetailView,
                                  CreateView,
                                  DeleteView,
                                  UpdateView,
                                  View,
                                  )

class TournDetailView(DetailView):
    model = Tournament
    template_name = 'tourn-detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tourn = kwargs.pop('object')

        try:
            if Entry.objects.filter(user=self.request.user, tournament=tourn).count() == 0:
                entered = False
            else:
                entered = True
        except:
            entered = False
        
        if Tournament.objects.get(pk=tourn.pk).date == datetime.datetime.today().date():
            live = True
        else:
            live = False

        context["entered"] = entered
        context['live'] = live
        context["sched"] = Schedule.objects.get(tournament=self.object.id)
        return context

@login_required
def TournUserView(request):
    past_tourns = Tournament.objects.filter(Q(user=request.user) & Q(date__lt=datetime.datetime.today().date())).order_by('-date')
    future_tourns = Tournament.objects.filter(Q(user=request.user) & Q(date__gte=datetime.datetime.today().date())).order_by('date')
    future_tourn_filter = TournUserFilter(request.GET, queryset=future_tourns)
    past_tourn_filter = TournUserFilter(request.GET, queryset=past_tourns)

    return render(request, 'user-tourn-list.html', {'filterFuture': future_tourn_filter,
                                                    'filterPast': past_tourn_filter, 
                                                    'tournaments': past_tourns, 
                                                    'tournamentsFuture': future_tourns})

class TournUserDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Tournament
    template_name = 'user-tourn-detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entries"] = Entry.objects.filter(tournament=self.object.id).order_by('rank')
        context["num"] = Entry.objects.filter(tournament=self.object.id).count()
        context["sched"] = Schedule.objects.get(tournament=self.object.id)

        if Tournament.objects.get(pk=self.object.id).date == datetime.datetime.today().date():
            live = True
        else: 
            live = False
        context['live'] = live
        
        return context
    
    def test_func(self):
        entry = self.get_object()
        if self.request.user == entry.user:
            return True
        else:
            logout(self.request) 
            messages.success(self.request, f"Please login to valid account to carry out this action!")
            return False
        

class TournCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Tournament
    form_class = TournForm
    template_name = 'tourn-create.html'
    success_url = ''
    success_message = "Your event has been created!"
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        meetTime = str(form.cleaned_data.get('meetTime'))
        #Take start time out of form but make sure to update start time if meet time is updated???
        form.instance.endTime = datetime.datetime.strptime(meetTime, '%H:%M:%S') + datetime.timedelta(hours=2, minutes=30)
        form.save()

        return super().form_valid(form)
    
    def get_success_url(self):
        success_url = reverse("user-tourn-list")
        return success_url 
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Event"
        context["return"] = "account"
        return context

class TournDeleteView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView):
    model = Tournament
    success_url = ''
    success_message = "Event deleted."

    def test_func(self):
        entry = self.get_object()
        if self.request.user == entry.user:
            return True
        return False

    def get_success_url(self):
        success_url = reverse("user-tourn-list")
        return success_url
    
class TournUpdateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = Tournament
    form_class = TournForm
    template_name = 'tourn-create.html'
    success_url = ''
    success_message = "Your event has been updated!"

    def form_valid(self, form):
        return super().form_valid(form)
    
    def test_func(self):
        entry = self.get_object()
        if self.request.user == entry.user:
            return True
        return False
    
    def get_success_url(self):
        success_url = reverse("user-tourn-detail", kwargs={'pk': self.object.id})
        return success_url
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update Event"
        context["return"] = self.object.id
        return context 

#ENTRIES

class EntryCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Entry
    form_class = EntryForm
    template_name = 'entry-create.html'
    success_url = ''
    success_message = "Event entered successfully!"
    
    def get_success_url(self):
        if self.request.user.groups.filter(name="Admin").exists():
            tourn = self.object.tournament.id
            return reverse_lazy('user-tourn-detail', kwargs={'pk': tourn})
        else:
            tourn = self.object.tournament.id
            return reverse_lazy('tourn-detail', kwargs={'pk': tourn})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Enter Event"
        context["return"] = "account"
        tourn = Tournament.objects.get(pk=self.kwargs.get('pk'))
        context['email'] = tourn.user.email
        return context
    
    def form_valid(self, form):
        if form.instance.user == '':
            form.instance.user = self.request.user
        
        if self.kwargs.get('pk') != 0:
            form.instance.tournament = Tournament.objects.get(pk=self.kwargs.get('pk'))

        #Create Order and Order Item for entry
        userId = form.instance.user.pk
        user = User.objects.get(pk=userId)
        new_order = Order.objects.create(
                                        title='Order 69',
                                        user=user,
                                        date=datetime.datetime.today().date()
                                        )
        new_order.title = f'Order #{new_order.id}'
        new_order.save()

        new_order_item = OrderItem.objects.create(
                                        order=Order.objects.get(id=new_order.id),
                                        tournament=form.instance.tournament,
                                        qty=1,
                                        price=form.instance.tournament.entryPrice,
                                        )
        new_order_item.save()

        redirect_url = super(EntryCreateView, self).form_valid(form)
        return redirect_url
    
    def get_form_kwargs(self, **kwargs):
        kwargs = super(EntryCreateView, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['tourn'] = Tournament.objects.get(pk=self.kwargs.get('pk'))
        return kwargs

@login_required
def EntryUserView(request):
    future_entries = Entry.objects.filter(Q(user=request.user) & Q(tournament__date__gte=datetime.datetime.today().date())).order_by('tournament__date')
    past_entries = Entry.objects.filter(Q(user=request.user) & Q(tournament__date__lt=datetime.datetime.today().date())).order_by('-tournament__date')
    future_entry_filter = EntryUserFilter(request.GET, queryset=future_entries)
    past_entry_filter = EntryUserFilter(request.GET, queryset=past_entries)

    return render(request, 'user-entry-list.html', {'filterFuture': future_entry_filter,
                                                    'filterPast': past_entry_filter, 
                                                    'entriesFuture': future_entries, 
                                                    'entriesPast': past_entries})

class EntryUpdateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = Entry
    form_class = EntryUpdateForm
    template_name = 'entry-create.html'
    success_url = ''
    success_message = "Entry updated!"

    def form_valid(self, form):
        try:
            Entry.objects.get(user=form.instance.user ,teamName=form.instance.teamName, tournament=form.instance.tournament)
        except Entry.DoesNotExist:
            pass
        else:
            if Entry.objects.get(user=form.instance.user ,teamName=form.instance.teamName, tournament=form.instance.tournament) != Entry.objects.get(pk=form.instance.pk):
                print('error')
                form.add_error('teamName', 'Entry with this team name already exists! Please choose a different team name.')
                return self.form_invalid(form)
                
        return super().form_valid(form)
    
    def test_func(self):
        entry = self.get_object()
        if self.request.user == entry.user:
            return True
        elif self.request.user.groups.filter(name="Admin").exists():
            return True
        else:
            return False
    
    def get_success_url(self):
        if self.request.user.groups.filter(name="Admin").exists():
            tourn = self.object.tournament.id
            return reverse_lazy('user-tourn-detail', kwargs={'pk': tourn})
        else:
            success_url = reverse("user-entry-list")
            return success_url 
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update Entry"
        kwargs['tourn'] = self.object.tournament.id
        context['email'] = self.object.tournament.user.email
        return context
    
    def get_form_kwargs(self, **kwargs):
        kwargs = super(EntryUpdateView, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['tourn'] = self.object.tournament
        return kwargs
    
class EntryDeleteView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView):
    model = Entry
    success_url = ''
    success_message = "Entry deleted."
    template_name = "entry-delete.html"

    def test_func(self):
        entry = self.get_object()
        if self.request.user == entry.user:
            return True
        elif self.request.user.groups.filter(name="Admin").exists():
            return True
        else:
            return False

    def get_success_url(self):
        tourn = self.object.tournament.id
        return reverse_lazy('user-tourn-detail', kwargs={'pk': tourn})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["return"] = self.object.tournament.id
        context["entry"] = self.object.teamName
        context["league"] = False
        return context

@login_required  
def EntryRequestDelete(request, pk):
    entry = Entry.objects.get(id=pk) 
    tournId = entry.tournament.id
    email = entry.tournament.user.email
    subject = 'Entry Request Delete'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email,]
    text_content = 'Text'
    html_content = render_to_string(
        'email.html',
        {'pk': tournId,
         'entry': entry,
         'tourn': entry.tournament,}
    )
    msg = EmailMultiAlternatives(subject, text_content, email_from, recipient_list)
    msg.attach_alternative(html_content, "text/html")
    msg.send()

    messages.success(request, f'Delete request sent!') 
    return redirect(reverse('user-entry-list'))

    
# MATCHES

class MatchTableView(DetailView):
    model = Tournament
    template_name = 'match-table.html'
    
    def get_context_data(self,*args, **kwargs):
        context = super(MatchTableView, self).get_context_data(*args,**kwargs)
        schedule = []
        start = Match.objects.filter(Q(tournament=self.object.id)).values('start').distinct().order_by('start')
        length = start.count()

        for i in range(length):
            qs = Match.objects.filter(Q(tournament=self.object.id) & Q(start=start[i].get('start'))).order_by('pitch')
            row = []

            row.append(qs.first())
            for j in range(len(qs)):
                row.append(qs[j])

            
            while len(row) < (self.object.noPitches + 1):
                row.append('blank')

            schedule.append(row)

        noPlayedMatches = Match.objects.filter(Q(tournament=self.object.id) & Q(played=True)).count()
        matches = Match.objects.filter(Q(tournament=self.object.id) & ~Q(division=0))
        matchCount = 0
        for match in matches:
            if not(match.entryOne == match.entryTwo):
                matchCount += 1

        if (noPlayedMatches >= matchCount):
            knockout = True
        else:
            knockout = False

        context['schedule'] = schedule
        context['sched'] = Schedule.objects.get(tournament=self.object.id)
        context['range'] = range(self.object.noPitches)
        context['return'] = self.object.id
        context['knockout'] = knockout
        return context
    
class MatchUpdateView(SuccessMessageMixin, UpdateView):
    model = Match
    form_class = ResultForm
    success_url = ''
    success_message = 'Result successfully updated!'
    template_name = 'match-result.html'

    def form_valid(self, form):
        form.instance.user = self.request.user
        prevMatch = Match.objects.get(pk=form.instance.pk)
        EntryUpdateThread(form.instance, prevMatch).start()
        return super().form_valid(form)
    
    def get_success_url(self):
        if self.object.played == True:
            tourn = self.object.tournament.id
            success_url = reverse("match-table", kwargs={"pk": tourn})
        else:
            success_url = reverse("match-result", kwargs={"pk": self.object.id})
        return success_url
    
class MatchListView(DetailView):
    model = Tournament
    template_name = 'match-list.html'
    
    def get_context_data(self,*args, **kwargs):
        context = super(MatchListView, self).get_context_data(*args,**kwargs)
        matches = Match.objects.filter(Q(tournament=self.object.id) & Q(division=0))

        context['matches'] = matches
        context['return'] = self.object.id
        return context
    
class MatchKnockoutUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Match
    form_class = MatchKnockoutUpdateForm
    template_name = 'match-update.html'
    success_url = ''
    success_message = "Match updated successfully!"
    
    def get_success_url(self):
        tourn = self.object.tournament.id
        return reverse_lazy('match-list', kwargs={'pk': tourn})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tourn"] = self.object.tournament
        return context
    
    def form_valid(self, form):
        redirect_url = super().form_valid(form)
        return redirect_url

class TournCustomiseView(DetailView):
    model = Tournament
    template_name = "user-tourn-customise.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sched"] = Schedule.objects.get(tournament=self.object.id)

        return context
    
#Assign Entry to Division Drag & Drop
class ChangeEntryDivision(LoginRequiredMixin, View):

    @staticmethod
    def get(request, *args, **kwargs):
        emp_id= kwargs['emp_id']
        task_id= kwargs['task_id']

        div = emp_id
        entry = Entry.objects.get(id=task_id)
        entry.division = div
        entry.save()

        return redirect(reverse_lazy('entry_assign_div', kwargs={'pk': entry.tournament.id}))

class AssignEntryView(LoginRequiredMixin, View):

    @staticmethod
    def get(request, *args, **kwargs):
        tourn = Tournament.objects.get(id=kwargs['pk'])
        entries = Entry.objects.filter(tournament__id=kwargs['pk'])

        #dynamically change no. divs
        if request.GET.get('divs') != None:
            if tourn.noDivisions != request.GET.get('divs'):
                tourn.noDivisions = int(request.GET.get('divs'))
                print(tourn.noDivisions)
                tourn.save()

                #unassign enrties if their div is deleted
                for entry in entries:
                    if int(entry.division) > int(tourn.noDivisions):
                        print(tourn.noDivisions)
                        entry.division = 0
                        entry.save()

        unassigned = Entry.objects.filter(tournament__id=kwargs['pk'], division=0)

        context = {'divs': range(0,tourn.noDivisions), 
                   'entries': entries, 
                   'unassigned': unassigned,
                   'tourn': tourn,
                   'redirect': False,
                   }

        return render(request, 'entry-assign-division.html', context)
    
class AssignEntryClearView(LoginRequiredMixin, View):

    @staticmethod
    def get(request, *args, **kwargs):
        tourn = Tournament.objects.get(id=kwargs['pk'])
        entries = Entry.objects.filter(tournament__id=kwargs['pk'])

        for entry in entries:
            entry.division = 0
            entry.save()

        unassigned = Entry.objects.filter(tournament__id=kwargs['pk'], division=0)

        context = {'divs': range(0,tourn.noDivisions), 
                   'entries': entries, 
                   'unassigned': unassigned,
                   'tourn': tourn,
                   'redirect': False,
                   }

        return render(request, 'entry-assign-division.html', context)
    
class AssignEntryAutoView(LoginRequiredMixin, View):

    @staticmethod
    def get(request, *args, **kwargs):
        tourn = Tournament.objects.get(id=kwargs['pk'])
        entries = Entry.objects.filter(tournament__id=kwargs['pk'])

        count = 1
        for entry in entries:
            if count > tourn.noDivisions:
                count = 1

            entry.division = count
            entry.save()

            count += 1

        unassigned = Entry.objects.filter(tournament__id=kwargs['pk'], division=0)

        context = {'divs': range(0,tourn.noDivisions), 
                   'entries': entries, 
                   'unassigned': unassigned,
                   'tourn': tourn,
                   'redirect': False,
                   }

        return render(request, 'entry-assign-division.html', context)
    
class UnassignCheckView(LoginRequiredMixin, View):

    @staticmethod
    def get(request, *args, **kwargs):
        tourn = Tournament.objects.get(id=kwargs['pk'])
        entries = Entry.objects.filter(tournament__id=kwargs['pk'])
        print(request)
        unassigned = Entry.objects.filter(tournament__id=kwargs['pk'], division=0)
        
        try:
            if unassigned[0].division == 0:
                print('sup')

            return render(request, 'entry-assign-division.html', context)  
        except:
            context = {'divs': range(0,tourn.noDivisions), 
                    'entries': entries, 
                    'unassigned': unassigned,
                    'tourn': tourn,
                    }
            return render(request, 'entry-assign-division.html', context)
        
def search_bar_past(request):
    if request.method == 'GET':
        search_query = request.GET.get('data', None)
        date = request.GET.get('date', None)
        age = request.GET.get('age', None)
        gender = request.GET.get('gender', None)
        group = request.GET.get('group', None)

        filterFields = []
        kwargs = {
            'user': request.user,
            '{0}__{1}'.format('date', 'lt'): datetime.datetime.today().date(), 
        }
        filterFields.append(['date', date])
        filterFields.append(['age', age])
        filterFields.append(['gender', gender])
        filterFields.append(['group', group])

        empty = 0
        for item in filterFields:
            if item[1] != "" and item[1] != None:
                kwargs.update({item[0]: item[1]})
            else:
                empty += 1


        filters = Tournament.objects.filter(**kwargs).order_by('-date')

        if search_query == "All" or (search_query == "" and empty == 4):
            qs = Tournament.objects.filter(user=request.user, date__lt=datetime.datetime.today().date()).order_by('-date')
        
        elif search_query == "":
            qs = filters

        else:
            qsOne = Tournament.objects.filter(user=request.user, name__icontains = search_query, date__lt=datetime.datetime.today().date()).order_by('-date')
            qsTwo = Tournament.objects.filter(user=request.user, gender__icontains = search_query, date__lt=datetime.datetime.today().date()).order_by('-date')
            qsThree = Tournament.objects.filter(user=request.user, group__icontains = search_query, date__lt=datetime.datetime.today().date()).order_by('-date')
            qsFour = Tournament.objects.filter(user=request.user, date__icontains = search_query, date__lt=datetime.datetime.today().date()).order_by('-date')
            qsFive = Tournament.objects.filter(user=request.user, venue__icontains = search_query, date__lt=datetime.datetime.today().date()).order_by('-date')
            qsSix = Tournament.objects.filter(user=request.user, level__icontains = search_query, date__lt=datetime.datetime.today().date()).order_by('-date')

            qs = qsOne | qsTwo | qsThree | qsFour | qsFive | qsSix

        data = dict()
        data['result'] = render_to_string(template_name='include/user-past-tourns.html',
                                        request=request,
                                        context={'tournaments': qs,
                                                }
                                        )
        return JsonResponse(data)

def search_bar_future(request):
    if request.method == 'GET':
        search_query = request.GET.get('data', None)
        date = request.GET.get('date', None)
        age = request.GET.get('age', None)
        gender = request.GET.get('gender', None)
        group = request.GET.get('group', None)

        filterFields = []
        kwargs = {
            'user': request.user,
            '{0}__{1}'.format('date', 'gte'): datetime.datetime.today().date(), 
        }
        filterFields.append(['date', date])
        filterFields.append(['age', age])
        filterFields.append(['gender', gender])
        filterFields.append(['group', group])

        empty = 0
        for item in filterFields:
            if item[1] != "" and item[1] != None:
                kwargs.update({item[0]: item[1]})
            else:
                empty += 1

        filters = Tournament.objects.filter(**kwargs).order_by('date')

        if search_query == "All" or (search_query == "" and empty == 4):
            qs = Tournament.objects.filter(user=request.user, date__gte=datetime.datetime.today().date()).order_by('date')
        
        elif search_query == "":
            qs = filters

        else:
            qsOne = Tournament.objects.filter(user=request.user, name__icontains = search_query, date__gte=datetime.datetime.today().date()).order_by('date')
            qsTwo = Tournament.objects.filter(user=request.user, gender__icontains = search_query, date__gte=datetime.datetime.today().date()).order_by('date')
            qsThree = Tournament.objects.filter(user=request.user, group__icontains = search_query, date__gte=datetime.datetime.today().date()).order_by('date')
            qsFour = Tournament.objects.filter(user=request.user, date__icontains = search_query, date__gte=datetime.datetime.today().date()).order_by('date')
            qsFive = Tournament.objects.filter(user=request.user, venue__icontains = search_query, date__gte=datetime.datetime.today().date()).order_by('date')
            qsSix = Tournament.objects.filter(user=request.user, level__icontains = search_query, date__gte=datetime.datetime.today().date()).order_by('date')

            qs = qsOne | qsTwo | qsThree | qsFour | qsFive | qsSix

        data = dict()
        data['result'] = render_to_string(template_name='include/user-future-tourns.html',
                                        request=request,
                                        context={'tournamentsFuture': qs,
                                                }
                                        )
        return JsonResponse(data)

def search_past_entries(request):
    if request.method == 'GET':
        month = request.GET.get('month', None)
        day = request.GET.get('day', None)
        year = request.GET.get('year', None)
        age = request.GET.get('age', None)
        gender = request.GET.get('gender', None)
        level = request.GET.get('level', None)

        filterFields = []
        kwargs = {
            'user': request.user,
            'tournament__{0}__{1}'.format('date', 'lt'): datetime.datetime.today().date(), 
        }
        
        filterFields.append(['tournament__age', age])
        filterFields.append(['tournament__gender', gender])
        filterFields.append(['tournament__level', level])
        filterFields.append(['tournament__date__month', month])
        filterFields.append(['tournament__date__day', day])
        filterFields.append(['tournament__date__year', year])


        empty = 0
        for item in filterFields:
            if item[1] != "" and item[1] != None:
                kwargs.update({item[0]: item[1]})
            else:
                empty += 1

        filters = Entry.objects.filter(**kwargs).order_by('-tournament__date')

        if empty == 6:
            qs = Entry.objects.filter(user=request.user, tournament__date__lt=datetime.datetime.today().date()).order_by('-tournament__date')
        else:
            qs = filters
        
        data = dict()
        data['result'] = render_to_string(template_name='include/user-past-entries.html',
                                        request=request,
                                        context={'entriesPast': qs,
                                                }
                                        )
        return JsonResponse(data)

def search_future_entries(request):
    if request.method == 'GET':
        month = request.GET.get('month', None)
        day = request.GET.get('day', None)
        year = request.GET.get('year', None)
        age = request.GET.get('age', None)
        gender = request.GET.get('gender', None)
        level = request.GET.get('level', None)

        filterFields = []
        kwargs = {
            'user': request.user,
            'tournament__{0}__{1}'.format('date', 'gte'): datetime.datetime.today().date(), 
        }
        
        filterFields.append(['tournament__age', age])
        filterFields.append(['tournament__gender', gender])
        filterFields.append(['tournament__level', level])
        filterFields.append(['tournament__date__month', month])
        filterFields.append(['tournament__date__day', day])
        filterFields.append(['tournament__date__year', year])

        empty = 0
        for item in filterFields:
            if item[1] != "" and item[1] != None:
                kwargs.update({item[0]: item[1]})
            else:
                empty += 1

        filters = Entry.objects.filter(**kwargs).order_by('tournament__date')

        if empty == 6:
            qs = Entry.objects.filter(user=request.user, tournament__date__gte=datetime.datetime.today().date()).order_by('tournament__date')
        else:
            qs = filters

        data = dict()
        data['result'] = render_to_string(template_name='include/user-future-entries.html',
                                        request=request,
                                        context={'entriesFuture': qs,
                                                }
                                        )
        return JsonResponse(data)
