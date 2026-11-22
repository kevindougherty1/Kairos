import zoneinfo

from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q


class Weekday(models.TextChoices):
    """Same day names the running engines use, so preferences pass straight through."""

    MON = "Mon", "Monday"
    TUE = "Tue", "Tuesday"
    WED = "Wed", "Wednesday"
    THU = "Thu", "Thursday"
    FRI = "Fri", "Friday"
    SAT = "Sat", "Saturday"
    SUN = "Sun", "Sunday"


class KairosUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        # The site owner (Kevin) is the coach.
        extra_fields.setdefault("role", User.Role.COACH)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """Kairos login. `role` decides what a person can see; it is never editable by the person themselves."""

    class Role(models.TextChoices):
        COACH = "coach", "Coach"
        CLIENT = "client", "Client"

    # Least privilege by default: a new account is a client until made a coach.
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CLIENT)

    objects = KairosUserManager()

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(role__in=["coach", "client"]), name="user_role_valid"),
        ]

    @property
    def is_coach(self):
        return self.role == self.Role.COACH

    @property
    def is_client(self):
        return self.role == self.Role.CLIENT


def validate_timezone(value):
    if value not in zoneinfo.available_timezones():
        raise ValidationError(f"{value!r} is not a known time zone (e.g. America/New_York).")


def validate_weekdays(values):
    unknown = set(values) - set(Weekday.values)
    if unknown:
        raise ValidationError(f"Unknown day(s): {', '.join(sorted(unknown))}.")


class Experience(models.TextChoices):
    BEGINNER = "beginner", "Beginner"
    INTERMEDIATE = "intermediate", "Intermediate"
    ADVANCED = "advanced", "Advanced"


class RaceDistance(models.IntegerChoices):
    """Race distances in metres (the internal unit)."""

    HALF_MARATHON = 21098, "Half Marathon (13.1 mi)"
    MARATHON = 42195, "Marathon (26.2 mi)"


class ClientProfile(models.Model):
    """Coaching details for one client. Edited by the coach, not the client."""

    class Units(models.TextChoices):
        MILES = "mi", "Miles"
        KILOMETRES = "km", "Kilometres"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_profile",
        limit_choices_to={"role": User.Role.CLIENT},
    )
    coach = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="clients",
        limit_choices_to={"role": User.Role.COACH},
    )

    # Goals and background
    goals = models.TextField(blank=True)
    training_background = models.TextField(blank=True)
    experience = models.CharField(max_length=12, choices=Experience.choices, blank=True)

    # Target race: the plan is built backward from this date (decision 2026-11-21).
    target_race_name = models.CharField(max_length=120, blank=True)
    target_race_date = models.DateField(null=True, blank=True)
    target_race_distance_m = models.PositiveIntegerField(
        choices=RaceDistance.choices, null=True, blank=True, help_text="Metres."
    )

    # Scheduling preferences (passed to the engines)
    runs_per_week = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(7)]
    )
    long_run_day = models.CharField(max_length=3, choices=Weekday.choices, default=Weekday.SAT)
    quality_day = models.CharField(max_length=3, choices=Weekday.choices, default=Weekday.TUE)
    unavailable_days = ArrayField(
        models.CharField(max_length=3, choices=Weekday.choices), default=list, blank=True,
        validators=[validate_weekdays],
    )
    preferred_rest_days = ArrayField(
        models.CharField(max_length=3, choices=Weekday.choices), default=list, blank=True,
        validators=[validate_weekdays],
    )

    # Display
    timezone = models.CharField(max_length=64, default="UTC", validators=[validate_timezone])
    preferred_units = models.CharField(max_length=2, choices=Units.choices, default=Units.MILES)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__first_name", "user__username"]
        constraints = [
            models.CheckConstraint(
                condition=Q(runs_per_week__isnull=True) | Q(runs_per_week__gte=1, runs_per_week__lte=7),
                name="clientprofile_runs_per_week_1_7",
            ),
        ]

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    def clean(self):
        if self.user_id and self.user.role != User.Role.CLIENT:
            raise ValidationError({"user": "Only client accounts can have a client profile."})
        if self.coach_id and self.coach.role != User.Role.COACH:
            raise ValidationError({"coach": "The assigned coach must have the coach role."})
        if self.user_id and self.user_id == self.coach_id:
            raise ValidationError({"coach": "A client can't be their own coach."})
