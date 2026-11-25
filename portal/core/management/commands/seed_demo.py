"""
Synthetic demo data: 1 coach + 2 clients with clearly labeled fixture plans.
These plans are hand-written placeholders, NOT engine output (brief §4: never present fixtures as real plans).

    .venv\\Scripts\\python.exe portal\\manage.py seed_demo
    .venv\\Scripts\\python.exe portal\\manage.py seed_demo --password "something-memorable"

Safe to re-run: it removes and rebuilds the demo accounts' fixture plans. Refuses to run with DEBUG off.
"""

import secrets
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import ClientProfile, Experience, RaceDistance, User
from core.units import miles_to_m
from training.models import PlanWeek, ScheduledWorkout, TrainingPlan, WorkoutResult, WorkoutType

COACH = ("demo_coach", "Demo", "Coach")
CLIENTS = [("demo_client_a", "Avery", "Demo"), ("demo_client_b", "Blake", "Demo")]

# (weekday offset, type, title, miles, prescription), a generic 2-week fixture pattern.
WEEK_PATTERN = [
    (0, WorkoutType.EASY, "Easy Run", 4, "Conversational pace."),
    (1, WorkoutType.THRESHOLD, "Speed Session", 6, "Warm up, 3 x 10 min at threshold with 2 min jog, cool down."),
    (3, WorkoutType.EASY, "Easy Run", 5, "Conversational pace, 6 x 20 sec strides at the end."),
    (5, WorkoutType.LONG_RUN, "Long Run", 10, "Easy effort throughout."),
]


class Command(BaseCommand):
    help = "Create or refresh demo users (1 coach, 2 clients) with fixture plans. Development only."

    def add_arguments(self, parser):
        parser.add_argument("--password", help="Password for all demo accounts (default: random, printed once).")

    @transaction.atomic
    def handle(self, *args, password=None, **options):
        if not settings.DEBUG:
            raise CommandError("seed_demo only runs with DJANGO_DEBUG=True (development).")
        password = password or secrets.token_urlsafe(9)

        coach = self._user(*COACH, role=User.Role.COACH, password=password)
        monday = timezone.localdate() - timedelta(days=timezone.localdate().weekday())

        for i, (username, first, last) in enumerate(CLIENTS):
            user = self._user(username, first, last, role=User.Role.CLIENT, password=password)
            profile, _ = ClientProfile.objects.update_or_create(user=user, defaults={
                "coach": coach,
                "goals": "[Demo] Run a strong half marathon.",
                "experience": Experience.INTERMEDIATE,
                "target_race_name": "[Demo] City Half Marathon",
                "target_race_date": monday + timedelta(weeks=12, days=6),
                "target_race_distance_m": RaceDistance.HALF_MARATHON,
                "runs_per_week": 4,
                "timezone": settings.TIME_ZONE,
            })
            # Rebuild this client's fixture plans from scratch.
            fixtures = TrainingPlan.objects.filter(client=profile, is_fixture=True)
            WorkoutResult.objects.filter(workout__week__plan__in=fixtures).delete()
            fixtures.delete()

            published = self._plan(profile, coach, monday, TrainingPlan.Status.PUBLISHED, f"Demo Block ({first})")
            if i == 0:
                # Client A also has a hidden draft (for isolation tests and the walkthrough)
                # and one logged result.
                self._plan(profile, coach, monday + timedelta(weeks=2), TrainingPlan.Status.DRAFT, "Demo Next Block (Draft)")
                first_workout = ScheduledWorkout.objects.filter(week__plan=published).order_by("date").first()
                WorkoutResult.objects.create(
                    workout=first_workout, status=WorkoutResult.Status.COMPLETED,
                    actual_distance_m=miles_to_m(4.2), actual_duration_s=40 * 60, perceived_effort=3,
                    comments="[Demo] Felt easy.", prescription_version=first_workout.version,
                )

        self.stdout.write(self.style.SUCCESS("Demo data ready (all plans are labeled fixtures)."))
        self.stdout.write(f"  Coach:   {COACH[0]}")
        for username, *_ in CLIENTS:
            self.stdout.write(f"  Client:  {username}")
        self.stdout.write(f"  Password for all three: {password}")

    def _user(self, username, first, last, role, password):
        user, _ = User.objects.update_or_create(username=username, defaults={
            "first_name": first, "last_name": last, "role": role,
            "email": f"{username}@example.com", "is_active": True,
        })
        user.set_password(password)
        user.save(update_fields=["password"])
        return user

    def _plan(self, profile, coach, monday, status, title):
        plan = TrainingPlan.objects.create(
            client=profile, title=title, plan_type="half_marathon", status=status,
            start_date=monday, end_date=monday + timedelta(days=13),
            created_by=coach, is_fixture=True,
            published_at=timezone.now() if status == TrainingPlan.Status.PUBLISHED else None,
        )
        for number in (1, 2):
            start = monday + timedelta(weeks=number - 1)
            week = PlanWeek.objects.create(
                plan=plan, number=number, start_date=start, phase="Base",
                target_distance_m=miles_to_m(sum(m for _, _, _, m, _ in WEEK_PATTERN)),
            )
            for offset, kind, label, miles, text in WEEK_PATTERN:
                ScheduledWorkout.objects.create(
                    week=week, date=start + timedelta(days=offset), workout_type=kind,
                    title=label, target_distance_m=miles_to_m(miles), prescription=text,
                )
        return plan
