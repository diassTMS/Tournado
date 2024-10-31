from .forms import LeagueForm, LeagueEntryForm, LeagueEntryUpdateForm, LeagueMatchUpdateForm, LeagueResultForm, PublishForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.decorators import login_required
from .filters import LeagueUserFilter, LeagueMatchFilter
from .models import League, LeagueEntry, LeagueMatch
from django.urls import reverse_lazy, reverse
from .threads import LeagueEntryUpdateThread
from django_filters.views import FilterView
from django.db.models.query import QuerySet
from django.shortcuts import render
from django.db.models import Q
import datetime
from django.views.generic import (DetailView,
                                  CreateView,
                                  DeleteView,
                                  UpdateView,
                                  ListView,
                                  )

#LEAGUES

@login_required
def LeagueUserView(request):
    leagues = League.objects.filter(user=request.user).order_by('startDate')
    league_filter = LeagueUserFilter(request.GET, queryset=leagues)

    return render(request, 'leagues/user-league-list.html', {'filter': league_filter})

class LeagueDetailView(DetailView):
    model = League
    template_name = 'leagues/league-detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        league = kwargs.pop('object')

        try:
            if LeagueEntry.objects.filter(user=self.request.user, league=league.id).count() == 0:
                entered = False
            else:
                entered = True
        except:
            entered = False
        
        if (League.objects.get(pk=self.object.id).startDate <= datetime.datetime.today().date()) and (League.objects.get(pk=self.object.id).endDate >= datetime.datetime.today().date()):
            live = True
        else:
            live = False

        context["entered"] = entered
        context['live'] = live
        return context

class LeagueUserDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = League
    template_name = 'leagues/user-league-detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entries"] = LeagueEntry.objects.filter(league=self.object.id)
        context["num"] = LeagueEntry.objects.filter(league=self.object.id).count()

        ongoing = League.objects.filter(pk=self.object.id, endDate__gte=datetime.date.today(), startDate__lte=datetime.date.today())
        if len(ongoing) != 0:
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
            return False
        
class LeagueCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = League
    form_class = LeagueForm
    template_name = 'leagues/league-create.html'
    success_url = ''
    success_message = "Your league has been created!"
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        success_url = reverse("user-league-list")
        return success_url 
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create League"
        context["return"] = "account"
        return context
    
class LeagueUpdateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = League
    form_class = LeagueForm
    template_name = 'leagues/league-create.html'
    success_url = ''
    success_message = "Your league has been updated!"

    def form_valid(self, form):
        return super().form_valid(form)
    
    def test_func(self):
        entry = self.get_object()
        if self.request.user == entry.user:
            return True
        return False
    
    def get_success_url(self):
        success_url = reverse("user-league-detail", kwargs={'pk': self.object.id})
        return success_url
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update League"
        context["return"] = self.object.id
        return context

class LeagueDeleteView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView):
    model = League
    success_url = ''
    success_message = "League deleted."

    def test_func(self):
        entry = self.get_object()
        if self.request.user == entry.user:
            return True
        return False

    def get_success_url(self):
        success_url = reverse("user-league-list")
        return success_url
    
class LeaguePublishView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = League
    form_class = PublishForm
    success_url = ''
    template_name = 'leagues/league-publish.html'
    success_message = "Your league has been published!"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
    
    def test_func(self):
        entry = self.get_object()
        if self.request.user == entry.user:
            return True
        return False
    
    def get_success_url(self):
        success_url = reverse("league-match-list", kwargs={'pk': self.object.id})
        return success_url
    
#LEAGUE ENTRIES

class LeagueEntryCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = LeagueEntry
    form_class = LeagueEntryForm
    template_name = 'entry-create.html'
    success_url = ''
    success_message = "League entered successfully!"
    
    def get_success_url(self):
        if self.request.user.groups.filter(name="Admin").exists():
            league = self.object.league.id
            return reverse_lazy('user-league-detail', kwargs={'pk': league})
        else:
            success_url = reverse("account")
            return success_url 
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Enter League"
        context["return"] = "account"
        league = League.objects.get(pk=self.kwargs.get('pk'))
        context['email'] = league.user.email
        return context
    
    def form_valid(self, form):
        if form.instance.user == '':
            form.instance.user = self.request.user
        
        if self.kwargs.get('pk') != 0:
            form.instance.league = League.objects.get(pk=self.kwargs.get('pk'))

        redirect_url = super(LeagueEntryCreateView, self).form_valid(form)
        return redirect_url
    
    def get_form_kwargs(self, **kwargs):
        kwargs = super(LeagueEntryCreateView, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['league'] = self.kwargs.get('pk')
        return kwargs

class LeagueEntryUpdateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = LeagueEntry
    form_class = LeagueEntryUpdateForm
    template_name = 'entry-create.html'
    success_url = ''
    success_message = "Team name updated!"

    def form_valid(self, form):
        try:
            LeagueEntry.objects.get(user=form.instance.user ,teamName=form.instance.teamName, league=form.instance.league)
        except LeagueEntry.DoesNotExist:
            pass
        else:
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
            league = self.object.league.id
            return reverse_lazy('user-league-detail', kwargs={'pk': league})
        else:
            success_url = reverse("user-league-list")
            return success_url 
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update League Entry"
        context['email'] = self.object.league.user.email
        return context
    
    def get_form_kwargs(self, **kwargs):
        kwargs = super(LeagueEntryUpdateView, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['league'] = self.object.league.id
        return kwargs
    
class LeagueEntryDeleteView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView):
    model = LeagueEntry
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
        league = self.object.league.id
        return reverse_lazy('user-league-detail', kwargs={'pk': league})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["return"] = self.object.league.id
        context["entry"] =self.object.teamName
        context["league"] = True
        return context

class LeagueMatchFilterView(FilterView):
    model = LeagueMatch
    queryset = LeagueMatch.objects.all()
    template_name = 'leagues/user-match-list.html'
    filterset_class = LeagueMatchFilter
    context_object_name = 'matches'

    def get_queryset(self):
        league = self.kwargs.get('pk')
        return LeagueMatch.objects.filter(league=league)
    
    def get_context_data(self,*args, **kwargs):
        context = super(LeagueMatchFilterView, self).get_context_data(*args,**kwargs)
        matches = LeagueMatch.objects.filter(league=self.kwargs.get('pk')).count()

        context['return'] = self.kwargs.get('pk')
        context['num'] = matches

        dataTrue = LeagueMatch.objects.filter(Q(league=self.kwargs.get('pk')) & Q(data=True)).count()
        if matches == dataTrue:
            context['allData'] = True
        else:
            context['allData'] = False

        return context
    
class LeagueMatchListView(FilterView):
    model = LeagueMatch
    queryset = LeagueMatch.objects.all()
    template_name = 'leagues/match-list.html'
    filterset_class = LeagueMatchFilter
    context_object_name = 'matches'

    def get_queryset(self):
        league = self.kwargs.get('pk')
        return LeagueMatch.objects.filter(league=league)
    
    def get_context_data(self,*args, **kwargs):
        context = super(LeagueMatchListView, self).get_context_data(*args,**kwargs)
        matches = LeagueMatch.objects.filter(league=self.kwargs.get('pk')).count()

        context['return'] = self.kwargs.get('pk')
        context['num'] = matches

        return context
    
class LeagueMatchUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = LeagueMatch
    form_class = LeagueMatchUpdateForm
    template_name = 'leagues/match-update.html'
    success_url = ''
    success_message = "Match updated successfully!"
    
    def get_success_url(self):
        league = self.object.league.id
        return reverse_lazy('league-match-list', kwargs={'pk': league})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["league"] = self.object.league
        return context
    
    def form_valid(self, form):
        if form.instance.venue != " " and form.instance.date != "" and form.instance.start != "":
            form.instance.data = True
            print('True')
        else:
            form.instance.data = False
            print('False')
        form.save()
        redirect_url = super().form_valid(form)
        return redirect_url
    
class LeagueMatchResultView(SuccessMessageMixin, UpdateView):
    model = LeagueMatch
    form_class = LeagueResultForm
    success_url = ''
    success_message = 'Result successfully updated!'
    template_name = 'leagues/match-result.html'

    def form_valid(self, form):
        form.instance.user = self.request.user
        prevMatch = LeagueMatch.objects.get(pk=form.instance.pk)
        LeagueEntryUpdateThread(form.instance, prevMatch).start()
        return super().form_valid(form)
    
    def get_success_url(self):
        if self.object.played == True:
            league = self.object.league.id
            success_url = reverse("league-match-list", kwargs={"pk": league})
        else:
            success_url = reverse("league-match-result", kwargs={"pk": self.object.id})
        return success_url
            