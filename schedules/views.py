from .forms import SchedulePDFForm, ScheduleForm, LeagueScheduleForm, TimingsForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .threads import GenerateScheduleThread, GenerateLeagueScheduleThread
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic.edit import FormMixin
from django.views.generic import UpdateView, DetailView, View
from leagues.models import League, LeagueEntry, LeagueMatch
from django.contrib.auth.decorators import login_required
from tournaments.models import Entry, Match, Tournament, SplitDivTimings
from django.shortcuts import HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, render, redirect
from .models import Schedule, Timings, Rules, PitchNames
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

    def form_invalid(self, form, **kwargs):
        print(form.errors)
        messages.error(self.request, form.errors.as_text())
        return self.render_to_response(self.get_context_data(form=form, **kwargs))
    
    def get_success_url(self):
        tourn = self.object.id
        time.sleep(5)

        return reverse_lazy('drag-drop', kwargs={'pk': tourn})

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

def publish_umpire_schedule(request, pk):
    sched = get_object_or_404(Schedule, id=pk)
    if sched.umpire_published == True:
        sched.umpire_published = False
        sched.save()
        messages.success(request, 'Umpire schedule unpublished!')
    else:
        sched.umpire_published = True
        sched.save()
        messages.success(request, 'Umpire schedule published!')
    
    return redirect(reverse_lazy('user-tourn-detail',  kwargs={'pk': sched.tournament.id}))

class SchedulePDFView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = Schedule
    form_class = SchedulePDFForm
    success_message = 'Your pdf is currently being generated!'       
    template_name = "schedule-pdf.html" 
    
    def form_valid(self, form):        
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
        data = {}
        tournament = Tournament.objects.get(pk=pk)
        sched = Schedule.objects.get(tournament__id=tournament.id)
        splitDivs = tournament.splitDivs
        playoffs = tournament.knockoutRounds
        allPitches = list(PitchNames.objects.filter(schedule=sched))

        def build_schedule(tournament_id, division_id, no_pitches):
            """Return schedule (list of rows) for a given division."""
            starts = (
                Match.objects.filter(tournament=tournament_id, division=division_id)
                .values_list("start", flat=True)
                .distinct()
                .order_by("start")
            )

            schedule = []
            for start_time in starts:
                qs = (
                    Match.objects.filter(
                        tournament=tournament_id, division=division_id, start=start_time
                    )
                    .order_by("pitch")
                )

                row = [qs.first()] + list(qs)
                # Pad with blanks until row length matches pitch count + 1
                row.extend(["blank"] * (no_pitches + 1 - len(row)))
                schedule.append(row)

            return schedule

        if splitDivs:
            divSchedules, divTimings, pitches = [], [], []
            index = 0
            div_range = (
                range(tournament.noDivisions + 1)
                if playoffs != "None"
                else range(tournament.noDivisions)
            )

            for div in div_range:
                div_number = 0 if (playoffs != "None" and div + 1 > tournament.noDivisions) else div + 1
                division = SplitDivTimings.objects.get(
                    tournament=tournament.id, divNumber=div_number
                )

                # Build schedule
                schedule = build_schedule(tournament.id, div_number, division.noPitches)
                divSchedules.append(schedule)

                # Build timings form
                divTiming = {"matchDuration": division.matchDuration,
                            "breakDuration": division.breakDuration,
                            "halftimeDuration": division.halftimeDuration,
                            "startTime": division.startTime,
                            "matchType": division.matchType,
                        },

                divTimings.append(divTiming)

                # Pitch allocations
                if div_number == 0:  # playoffs
                    pitches.append(allPitches)
                else:
                    num_pitches = division.noPitches
                    pitches.append(allPitches[index : index + num_pitches])
                    index += num_pitches

            # Bundle everything into context["divisions"]
            data["divisions"] = [
                {
                    "timings": divTimings[i][0],
                    "schedule": divSchedules[i],
                    "pitches": pitches[i],
                }
                for i in range(len(divSchedules))
            ]

            timingsExtra = Timings.objects.filter(schedule=sched)
            rules = Rules.objects.filter(schedule=sched)
            timed = sched.timed

            data.update(
                {
                    'timingsExtra': timingsExtra,
                    'rules': rules,
                    'timed': timed,
                }
            )

        else:
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

            
                schedule.append(row) 
            
            sched = Schedule.objects.get(tournament=tournament) 
            pitches = PitchNames.objects.filter(schedule=sched) 
            timingsExtra = Timings.objects.filter(schedule=sched)
            rules = Rules.objects.filter(schedule=sched)
            timed = sched.timed

            timings = {"matchDuration": tournament.matchDuration,
                    "breakDuration": tournament.breakDuration,
                    "halftimeDuration": tournament.halftimeDuration,
                    "startTime": tournament.startTime,
                    "matchType": tournament.matchType,
                }
            
            data.update(
                {
                    "schedule": schedule,
                    "pitches": pitches,
                    "timings": timings,
                    'timingsExtra': timingsExtra,
                    'rules': rules,
                    'timed': timed,
                }
            )

        data.update(
            {
                "tourn": tournament,
                "schedId": sched,
            }
        )

        return renderers.render_to_pdf('pdf.html', data)

class UmpirePDFView(View):    
    def get(self, request, pk):
        data = {}
        tournament = Tournament.objects.get(pk=pk)
        sched = Schedule.objects.get(tournament__id=tournament.id)
        splitDivs = tournament.splitDivs
        playoffs = tournament.knockoutRounds
        allPitches = list(PitchNames.objects.filter(schedule=sched))

        def build_schedule(tournament_id, division_id, no_pitches):
            """Return schedule (list of rows) for a given division."""
            starts = (
                Match.objects.filter(tournament=tournament_id, division=division_id)
                .values_list("start", flat=True)
                .distinct()
                .order_by("start")
            )

            schedule = []
            for start_time in starts:
                qs = (
                    Match.objects.filter(
                        tournament=tournament_id, division=division_id, start=start_time
                    )
                    .order_by("pitch")
                )

                row = [qs.first()] + list(qs)
                # Pad with blanks until row length matches pitch count + 1
                row.extend(["blank"] * (no_pitches + 1 - len(row)))
                schedule.append(row)

            return schedule

        if splitDivs:
            divSchedules, divTimings, pitches = [], [], []
            index = 0
            div_range = (
                range(tournament.noDivisions + 1)
                if playoffs != "None"
                else range(tournament.noDivisions)
            )


            for div in div_range:
                div_number = 0 if (playoffs != "None" and div + 1 > tournament.noDivisions) else div + 1
                division = SplitDivTimings.objects.get(
                    tournament=tournament.id, divNumber=div_number
                )

                # Build schedule
                schedule = build_schedule(tournament.id, div_number, division.noPitches)
                divSchedules.append(schedule)

                # Build timings form
                divTiming = {"matchDuration": division.matchDuration,
                            "breakDuration": division.breakDuration,
                            "halftimeDuration": division.halftimeDuration,
                            "startTime": division.startTime,
                            "matchType": division.matchType,
                        },

                divTimings.append(divTiming)

                # Pitch allocations
                if div_number == 0:
                    pitches.append(allPitches)
                else:
                    num_pitches = division.noPitches
                    pitches.append(allPitches[index : index + num_pitches])
                    index += num_pitches

            # Bundle everything into context["divisions"]
            data["divisions"] = [
                {
                    "timings": divTimings[i][0],
                    "schedule": divSchedules[i],
                    "pitches": pitches[i],
                }
                for i in range(len(divSchedules))
            ]

            timingsExtra = Timings.objects.filter(schedule=sched)
            rules = Rules.objects.filter(schedule=sched)
            timed = sched.timed

            data.update(
                {
                    'timingsExtra': timingsExtra,
                    'rules': rules,
                    'timed': timed,
                }
            )

        else:
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
            
                schedule.append(row) 
            
            sched = Schedule.objects.get(tournament=tournament) 
            pitches = PitchNames.objects.filter(schedule=sched) 
            timingsExtra = Timings.objects.filter(schedule=sched)
            rules = Rules.objects.filter(schedule=sched)
            timed = sched.timed

            timings = {"matchDuration": tournament.matchDuration,
                    "breakDuration": tournament.breakDuration,
                    "halftimeDuration": tournament.halftimeDuration,
                    "startTime": tournament.startTime,
                    "matchType": tournament.matchType,
                }
            
            data.update(
                {
                    "schedule": schedule,
                    "pitches": pitches,
                    "timings": timings,
                    'timingsExtra': timingsExtra,
                    'rules': rules,
                    'timed': timed,
                }
            )

        data.update(
            {
                "tourn": tournament,
                "schedId": sched,
            }
        )

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
    
class DragDropView(FormMixin, DetailView):
    model = Tournament
    template_name = 'drag-drop.html'
    form_class = TimingsForm
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        sched = Schedule.objects.get(tournament__id=self.object.id)
        splitDivs = self.object.splitDivs
        playoffs = self.object.knockoutRounds
        allPitches = list(PitchNames.objects.filter(schedule=sched))

        def build_schedule(tournament_id, division_id, no_pitches):
            """Return schedule (list of rows) for a given division."""
            starts = (
                Match.objects.filter(tournament=tournament_id, division=division_id)
                .values_list("start", flat=True)
                .distinct()
                .order_by("start")
            )

            schedule = []
            for start_time in starts:
                qs = (
                    Match.objects.filter(
                        tournament=tournament_id, division=division_id, start=start_time
                    )
                    .order_by("pitch")
                )

                row = [qs.first()] + list(qs)
                # Pad with blanks until row length matches pitch count + 1
                row.extend(["blank"] * (no_pitches + 1 - len(row)))
                schedule.append(row)

            return schedule

        if splitDivs:
            divSchedules, divTimings, pitches = [], [], []
            index = 0
            div_range = (
                range(self.object.noDivisions + 1)
                if playoffs != "None"
                else range(self.object.noDivisions)
            )

            for div in div_range:
                div_number = 0 if (playoffs != "None" and div + 1 > self.object.noDivisions) else div + 1
                division = SplitDivTimings.objects.get(
                    tournament=self.object.id, divNumber=div_number
                )

                # Build schedule
                schedule = build_schedule(self.object.id, div_number, division.noPitches)
                divSchedules.append(schedule)

                # Build timings form
                divTiming = TimingsForm(
                    auto_id=False,
                    initial={
                        "matchDuration": division.matchDuration,
                        "breakDuration": division.breakDuration,
                        "halftimeDuration": division.halftimeDuration,
                        "startTime": division.startTime,
                        "matchType": division.matchType,
                    },
                )
                divTiming.fields["matchType"].widget.attrs["id"] = f"matchType{div+1}"
                divTiming.fields["halftimeDuration"].widget.attrs["id"] = f"halftime{div+1}"
                divTimings.append(divTiming)

                # Pitch allocations
                if div_number == 0:  # playoffs
                    pitches.append(allPitches)
                else:
                    num_pitches = division.noPitches
                    pitches.append(allPitches[index : index + num_pitches])
                    index += num_pitches

            # Bundle everything into context["divisions"]
            context["divisions"] = [
                {
                    "form": divTimings[i],
                    "schedule": divSchedules[i],
                    "pitches": pitches[i],
                }
                for i in range(len(divSchedules))
            ]

        else:
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
            
                schedule.append(row) 
            
            sched = Schedule.objects.get(tournament=self.object) 
            pitches = PitchNames.objects.filter(schedule=sched) 

            form = TimingsForm(
                initial={
                    "matchDuration": self.object.matchDuration,
                    "breakDuration": self.object.breakDuration,
                    "halftimeDuration": self.object.halftimeDuration,
                    "startTime": self.object.startTime,
                    "matchType": self.object.matchType,
                }
            )
            
            form.fields["matchType"].widget.attrs["id"] = f"matchType1"
            form.fields["halftimeDuration"].widget.attrs["id"] = f"halftime1"

            context.update(
                {
                    "schedule": schedule,
                    "pitches": pitches,
                    "form": form,
                }
            )

        context.update(
            {
                "tourn": self.object,
                "schedId": sched,
            }
        )

        return context

    def form_valid(self, form):
        tourn = form.instance.id
        return HttpResponseRedirect(reverse('drag-drop', kwargs={'pk': tourn}))
    
    def get_success_url(self):
        return reverse('drag-drop', kwargs={'pk': self.object.id})

    def post(self, request, *args, **kwargs):
        pk = kwargs.get('pk')

        def to_datetime(val):
            if isinstance(val, datetime.time):
                return datetime.datetime.combine(datetime.date.today(), val)
            return val

        def update_matches(matches, delta):
            for match in matches:
                match.start = (to_datetime(match.start) + delta).time()
                match.end = (to_datetime(match.end) + delta).time()
                match.save()

        if 'division_number' in request.POST:
            division_number = int(request.POST.get('division_number'))
            start_time = request.POST.get('startTime')
            match_type = request.POST.get('matchType')
            match_duration = int(request.POST.get('matchDuration'))
            break_duration = int(request.POST.get('breakDuration'))
            halftime_duration = int(request.POST.get('halftimeDuration'))

            tournament = Tournament.objects.get(pk=pk)
            playoff_div_number = tournament.noDivisions + 1  # Playoff form's division_number
            is_playoff = (division_number == playoff_div_number)

            # For SplitDivTimings and Match queries, use 0 for playoffs
            split_div_number = 0 if is_playoff else division_number
            match_division = 0 if is_playoff else division_number

            # --- Playoff validation ---
            if is_playoff:
                # Find latest end time in any non-playoff division
                latest_end = Match.objects.filter(tournament=pk).exclude(division=0).order_by('-end').values_list('end', flat=True).first()
                playoff_timing = SplitDivTimings.objects.filter(tournament=pk, divNumber=0).first()
                playoff_break_duration = int(playoff_timing.breakDuration) if playoff_timing else break_duration

                if latest_end:
                    latest_end_dt = to_datetime(latest_end)
                    min_playoff_start = latest_end_dt + datetime.timedelta(minutes=playoff_break_duration)

                    try:
                        new_playoff_time = datetime.datetime.strptime(start_time, '%H:%M:%S').time()
                    except ValueError:
                        new_playoff_time = datetime.datetime.strptime(start_time, '%H:%M').time()
                    new_playoff_start_dt = datetime.datetime.combine(datetime.date.today(), new_playoff_time)
                    
                    if new_playoff_start_dt < min_playoff_start:
                        messages.error(request, "Playoff matches cannot start before the last division match ends plus the playoff break duration.")
                        return HttpResponseRedirect(reverse('drag-drop', kwargs={'pk': pk}))

            # Update SplitDivTimings for this division (including playoffs)
            SplitDivTimings.objects.filter(tournament=pk, divNumber=split_div_number).update(
                matchDuration=match_duration,
                breakDuration=break_duration,
                halftimeDuration=halftime_duration,
                startTime=start_time,
                matchType=match_type,
            )

            # Update timings for matches in this division (including playoffs)
            rows = Match.objects.filter(tournament=pk, division=match_division).values('start').distinct().order_by('start')
            try:
                d = datetime.datetime.strptime(start_time, '%H:%M:%S')
            except ValueError:
                d = datetime.datetime.strptime(start_time, '%H:%M')

            duration = match_duration if match_type == "One Way" else (2 * match_duration) + halftime_duration

            for row in rows:
                qs = Match.objects.filter(tournament=pk, division=match_division, start=row['start']).order_by('pitch')
                start = d
                d += datetime.timedelta(minutes=duration)
                end = d
                d += datetime.timedelta(minutes=break_duration)
                for match in qs:
                    match.start = start
                    match.end = end
                    match.save()

            if is_playoff:
                # No shifting logic needed for playoffs, already updated above
                pass
            else:
                # Playoff shifting logic (only if a non-playoff division is changed)
                latest_end = Match.objects.filter(tournament=pk).exclude(division=0).order_by('-end').values_list('end', flat=True).first()
                first_playoff = Match.objects.filter(tournament=pk, division=0).order_by('start').first()
                playoff_timing = SplitDivTimings.objects.filter(tournament=pk, divNumber=0).first()
                playoff_break_duration = int(playoff_timing.breakDuration) if playoff_timing else break_duration

                if latest_end and first_playoff:
                    latest_end_dt = to_datetime(latest_end)
                    first_playoff_start_dt = to_datetime(first_playoff.start)
                    desired_playoff_start = latest_end_dt + datetime.timedelta(minutes=playoff_break_duration)

                    if desired_playoff_start != first_playoff_start_dt:
                        playoff_matches = list(Match.objects.filter(tournament=pk, division=0).order_by('start'))
                        if playoff_matches:
                            orig_first_start_dt = to_datetime(playoff_matches[0].start)
                            delta = desired_playoff_start - orig_first_start_dt
                            update_matches(playoff_matches, delta)
                            SplitDivTimings.objects.filter(tournament=pk, divNumber=0).update(startTime=desired_playoff_start.time())
        else:
            # Fallback for non-splitDivs tournaments
            form = self.get_form()
            start_time = form.data.get('startTime')
            match_type = form.data.get('matchType')
            match_duration = int(form.data.get('matchDuration'))
            break_duration = int(form.data.get('breakDuration'))
            halftime_duration = int(form.data.get('halftimeDuration'))

            Tournament.objects.filter(pk=pk).update(
                matchDuration=match_duration,
                breakDuration=break_duration,
                halftimeDuration=halftime_duration,
                startTime=start_time,
                matchType=match_type,
            )

            rows = Match.objects.filter(tournament=pk).values('start').distinct().order_by('start')
            try:
                d = datetime.datetime.strptime(start_time, '%H:%M:%S')
            except ValueError:
                d = datetime.datetime.strptime(start_time, '%H:%M')

            duration = match_duration if match_type == "One Way" else (2 * match_duration) + halftime_duration

            for row in rows:
                qs = Match.objects.filter(tournament=pk, start=row['start']).order_by('pitch')
                start = d
                d += datetime.timedelta(minutes=duration)
                end = d
                d += datetime.timedelta(minutes=break_duration)
                for match in qs:
                    match.start = start
                    match.end = end
                    match.save()

        return HttpResponseRedirect(reverse('drag-drop', kwargs={'pk': pk}))

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
    
def pitches_change(request):
    if request.method == 'GET':
        tourn_id = request.GET.get('id', None)
        noPitches = request.GET.get('pitches', None)

        tourn = Tournament.objects.get(pk=tourn_id)
        sched = Schedule.objects.get(tournament=tourn)

        tourn.noPitches = noPitches
        tourn.save()

        pitches = PitchNames.objects.filter(schedule=sched)
        while len(pitches) != int(noPitches):
            if len(pitches) < int(noPitches):
                pitchNew = PitchNames.objects.create(schedule=sched, name="")
                pitchNew.save()

            else:
                pitchOld = pitches.last()
                pitchOld.delete()

            pitches = PitchNames.objects.filter(schedule=sched)
        
    return redirect(reverse_lazy('schedule-create', kwargs={'pk': tourn_id}))