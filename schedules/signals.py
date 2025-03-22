from django.db.models.signals import post_save
from .models import Schedule, Timings, Rules, PitchNames
from tournaments.models import Tournament
from django.dispatch import receiver

@receiver(post_save, sender=Tournament, weak=False)
def create_sched(sender, instance, created, **kwargs):
    if created:
        sched = Schedule.objects.create(tournament=instance)
        print(sched)
        sched.save()

@receiver(post_save, sender=Schedule, weak=False)
def create_sched(sender, instance, created, **kwargs):
    if created:
        club_rules = [
            "Players & Coaches MUST wait off the pitch area between games",
            "Spectators MUST remain behind the barriers (Teams may have one coach, one manager and one umpire on the pitch area)",
            "No food on the playing areas please",
            "Each team is responsible for providing first aid - including ice packs",
            "The toss of a coin shall decide which team shall have the first push back or choice of end",
            "Match Ball: 1st named team to provide the match ball",
            "Clash of shirts: 2nd named team to change",
         ]
        
        school_rules = [
            "The toss of a coin shall decide which team shall have the first push back or choice of end",
            "Match Ball: 1st named team to provide the match ball",
            "Clash of shirts: 2nd named team to change",
            "Scoring Win = 3 points Draw = 1 point Loss = 0 points",
            "If, at the end of the division matches teams are equal on points, the rankings will be decided by:",
            "1. Goal difference",
            "2. Goals scored",
            "3. Highest number of matches won",
            "4. Winner of match between the two tied teams",
            "5. A penalty shoot out between the tied teams of 3 penalty shuffles (8sec 1v1) followed by sudden death shuffles if required",
            "Good Luck to all teams",
        ]

        if instance.tournament.group == "Club":
            for i in range(len(club_rules)):
                rule = Rules.objects.create(schedule=instance, rule=club_rules[i], order=(i+1))
                rule.save()
        else:
            for i in range(len(school_rules)):
                rule = Rules.objects.create(schedule=instance, rule=school_rules[i], order=(i+1))
                rule.save()
