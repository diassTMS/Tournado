import django_tables2 as tables
from django_tables2.utils import A
from django.utils.safestring import mark_safe
from tournaments.models import Entry, Match
from leagues.models import LeagueEntry

class ScoreTable(tables.Table):
    teamName = tables.LinkColumn("entry-stats",  text=lambda record: record.teamName, args=[A("pk")])
    goalDiff = tables.Column(verbose_name="GD",
                            attrs={
                                'th':{'style':'text-align: center;'},
                                'td':{'style':'text-align: center;'},
                            })
    played = tables.Column(verbose_name="Pld",
                           attrs={
                                'th':{'style':'text-align: center;'},
                                'td':{'style':'text-align: center;'},
                            })
    points = tables.Column(verbose_name="Pts",
                           attrs={
                                'th':{'style':'text-align: center;'},
                                'td':{'style':'text-align: center;'},
                            })

    class Meta:
        model = Entry
        template_name = "django_tables2/bootstrap4-responsive.html"
        fields = ("teamName", "played", "goalDiff", "points",)
        orderable = False

class LargeKnockoutTable(tables.Table):
    entryOne = tables.Column(verbose_name="Match")
    goalsOne = tables.Column(verbose_name="Score", 
                             attrs={
                                    'th':{'style':'text-align: center;'},
                                    'td':{'style':'text-align: center;'},
                                }
                            )
    start = tables.Column(verbose_name="Time")

    def render_entryOne(self, record, value):
        return mark_safe(f"{value.teamName} v. {record.entryTwo.teamName}")
    
    def render_goalsOne(self, record, value):
        if record.played == False:
            return mark_safe(f"-")
        elif record.goalsOne == record.goalsTwo:
            return mark_safe(f"{record.pfOne + record.goalsOne} - {record.pfTwo + record.goalsTwo} <br> PF")
        else:
            return mark_safe(f"{value} - {record.goalsTwo}")
        
    def render_start(self, record, value):
        start = value.strftime("%H:%M")
        end = record.end.strftime("%H:%M")
        return mark_safe(f"{start} - {end}")

    class Meta:
        model = Match
        template_name = "django_tables2/bootstrap4-responsive.html"
        fields = ("type", "pitch", "start", "entryOne", "goalsOne")
        orderable = False

class SmallKnockoutTable(tables.Table):
    entryOne = tables.Column(verbose_name="Match")
    goalsOne = tables.Column(verbose_name="Score")

    def render_entryOne(self, record, value):
        return mark_safe(f"{value.teamName} v. {record.entryTwo.teamName}")
    
    def render_goalsOne(self, record, value):
        if record.played == False:
            return mark_safe(f"-")
        elif record.goalsOne == record.goalsTwo:
            return mark_safe(f"{record.pfOne + record.goalsOne} - {record.pfTwo + record.goalsTwo} <br> PF")
        else:
            return mark_safe(f"{value} - {record.goalsTwo}")

    class Meta:
        model = Match
        template_name = "django_tables2/bootstrap4-responsive.html"
        fields = ("type", "entryOne", "goalsOne")
        orderable = False

class LeagueScoreTable(tables.Table):
    teamName = tables.LinkColumn("league-entry-stats",  text=lambda record: record.teamName, args=[A("pk")])
    goalDiff = tables.Column(verbose_name="GD",
                            attrs={
                                'th':{'style':'text-align: center;'},
                                'td':{'style':'text-align: center;'},
                            })
    played = tables.Column(verbose_name="Pld",
                           attrs={
                                'th':{'style':'text-align: center;'},
                                'td':{'style':'text-align: center;'},
                            })
    points = tables.Column(verbose_name="Pts",
                           attrs={
                                'th':{'style':'text-align: center;'},
                                'td':{'style':'text-align: center;'},
                            })
    forGoals = tables.Column(verbose_name="For",
                           attrs={
                                'th':{'style':'text-align: center;'},
                                'td':{'style':'text-align: center;'},
                            })
    againstGoals = tables.Column(verbose_name="Against",
                           attrs={
                                'th':{'style':'text-align: center;'},
                                'td':{'style':'text-align: center;'},
                            })
    won = tables.Column(verbose_name="Won",
                           attrs={
                                'th':{'style':'text-align: center;'},
                                'td':{'style':'text-align: center;'},
                            })
    drawn = tables.Column(verbose_name="Drawn",
                           attrs={
                                'th':{'style':'text-align: center;'},
                                'td':{'style':'text-align: center;'},
                            })
    lost = tables.Column(verbose_name="Lost",
                           attrs={
                                'th':{'style':'text-align: center;'},
                                'td':{'style':'text-align: center;'},
                            })

    class Meta:
        model = LeagueEntry
        template_name = "django_tables2/bootstrap4-responsive.html"
        fields = ("teamName", "played", "won", "drawn", "lost", "forGoals", "againstGoals", "goalDiff", "points")
        orderable = False