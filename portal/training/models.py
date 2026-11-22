"""
Training data. Internal units: distances in metres, durations in seconds (convert only for display,
see core/units.py). Calendar dates are the client's local dates (DateField, no time zone);
timestamps are UTC.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q

from accounts.models import ClientProfile, RaceDistance


class PlanType(models.TextChoices):
    HALF_MARATHON = "half_marathon", "Half Marathon"
    MARATHON = "marathon", "Marathon"
    SPEED = "speed", "Speed Block"
    BASE_ECONOMY = "base_economy", "Base / Running Economy Block"
    RECOVERY = "recovery", "Post-Race Recovery"
    MAINTENANCE = "maintenance", "Maintenance Block"


class TrainingPlan(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    client = models.ForeignKey(ClientProfile, on_delete=models.PROTECT, related_name="plans")
    title = models.CharField(max_length=150)
    plan_type = models.CharField(max_length=20, choices=PlanType.choices)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)

    start_date = models.DateField()
    end_date = models.DateField()

    # Race the plan is built toward (blank for non-race blocks).
    race_name = models.CharField(max_length=120, blank=True)
    race_date = models.DateField(null=True, blank=True)
    race_distance_m = models.PositiveIntegerField(choices=RaceDistance.choices, null=True, blank=True)

    # Provenance (brief §4): which generator made it, from which inputs.
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="plans_created")
    generator_version = models.CharField(
        max_length=100, blank=True, help_text="e.g. hm-v5.7@9ffcf6912cf4. Blank = written by the coach."
    )
    input_snapshot = models.JSONField(default=dict, blank=True)
    is_fixture = models.BooleanField(default=False, help_text="Synthetic demo data, not a real plan.")

    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date", "-created_at"]
        constraints = [
            models.CheckConstraint(condition=Q(end_date__gte=F("start_date")), name="plan_end_after_start"),
            # A client has at most one live plan; publishing a new one archives the old (Phase 2 service).
            models.UniqueConstraint(
                fields=["client"], condition=Q(status="published"), name="plan_one_published_per_client"
            ),
            models.CheckConstraint(
                condition=~Q(status="published") | Q(published_at__isnull=False),
                name="plan_published_has_timestamp",
            ),
        ]

    def __str__(self):
        prefix = "[Fixture] " if self.is_fixture else ""
        return f"{prefix}{self.title} ({self.get_status_display()})"

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "The end date can't be before the start date."})
        if self.race_date and self.start_date and self.end_date and not (
            self.start_date <= self.race_date <= self.end_date
        ):
            raise ValidationError({"race_date": "The race date must fall inside the plan."})


class PlanWeek(models.Model):
    """One week of a plan: phase, target volume and any generator warnings for the coach."""

    plan = models.ForeignKey(TrainingPlan, on_delete=models.CASCADE, related_name="weeks")
    number = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    start_date = models.DateField(help_text="The Monday of this week.")
    phase = models.CharField(max_length=20, blank=True)
    target_distance_m = models.PositiveIntegerField(null=True, blank=True)
    warnings = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["plan", "number"]
        constraints = [
            models.UniqueConstraint(fields=["plan", "number"], name="planweek_unique_number"),
            models.CheckConstraint(condition=Q(number__gte=1), name="planweek_number_positive"),
        ]

    def __str__(self):
        return f"Week {self.number}"


class WorkoutType(models.TextChoices):
    EASY = "easy", "Easy Run"
    LONG_RUN = "long_run", "Long Run"
    MEDIUM_LONG = "medium_long", "Medium-Long Run"
    TEMPO = "tempo", "Tempo"
    THRESHOLD = "threshold", "Threshold"
    VO2 = "vo2", "VO2 Intervals"
    RACE_PACE = "race_pace", "Race Pace"
    HILLS = "hills", "Hills"
    SPEED = "speed", "Speed Support"
    ECONOMY = "economy", "Economy / Strides"
    SHAKEOUT = "shakeout", "Shakeout"
    RACE = "race", "Race"
    CROSS_TRAINING = "cross_training", "Cross-Training"
    STRENGTH = "strength", "Strength"
    OTHER = "other", "Other"


class ScheduledWorkout(models.Model):
    """The prescription. What the client actually did lives in WorkoutResult, never here."""

    week = models.ForeignKey(PlanWeek, on_delete=models.CASCADE, related_name="workouts")
    date = models.DateField()
    order = models.PositiveSmallIntegerField(default=0, help_text="Order within the day (for doubles).")
    workout_type = models.CharField(max_length=20, choices=WorkoutType.choices)
    title = models.CharField(max_length=120)
    prescription = models.TextField(blank=True, help_text="What to do, e.g. '4 x 1 mile at threshold'.")
    target_distance_m = models.PositiveIntegerField(null=True, blank=True)
    target_duration_s = models.PositiveIntegerField(null=True, blank=True)
    coach_notes = models.TextField(blank=True)
    version = models.PositiveIntegerField(default=1, help_text="Bumped on each edit after publishing.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date", "order"]
        constraints = [
            models.UniqueConstraint(fields=["week", "date", "order"], name="workout_unique_slot"),
        ]

    def __str__(self):
        return f"{self.date:%a %d %b}: {self.title}"

    @property
    def plan(self):
        return self.week.plan

    def clean(self):
        if self.week_id and self.date:
            from datetime import timedelta

            if not (self.week.start_date <= self.date <= self.week.start_date + timedelta(days=6)):
                raise ValidationError({"date": "The date must fall inside its week."})


class PrescriptionRevision(models.Model):
    """Audit trail: the prescription as it was before each edit to a published workout,
    so results logged against an older version stay understandable (brief §6)."""

    workout = models.ForeignKey(ScheduledWorkout, on_delete=models.CASCADE, related_name="revisions")
    version = models.PositiveIntegerField()
    snapshot = models.JSONField(help_text="Prescription fields at this version.")
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    changed_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["workout", "version"]
        constraints = [
            models.UniqueConstraint(fields=["workout", "version"], name="revision_unique_version"),
        ]


class WorkoutResult(models.Model):
    """What the client actually did. One per workout (DB-enforced); re-submitting updates it.
    The client is derived from workout → week → plan → client, never submitted."""

    class Status(models.TextChoices):
        COMPLETED = "completed", "Completed"
        PARTIAL = "partial", "Partly Done"
        SKIPPED = "skipped", "Skipped"

    workout = models.OneToOneField(ScheduledWorkout, on_delete=models.PROTECT, related_name="result")
    status = models.CharField(max_length=10, choices=Status.choices)
    actual_distance_m = models.PositiveIntegerField(null=True, blank=True)
    actual_duration_s = models.PositiveIntegerField(null=True, blank=True)
    perceived_effort = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="RPE 1 (very easy) to 10 (max effort).",
    )
    comments = models.TextField(blank=True)
    prescription_version = models.PositiveIntegerField(
        default=1, help_text="Which version of the prescription this result was logged against."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(perceived_effort__isnull=True) | Q(perceived_effort__gte=1, perceived_effort__lte=10),
                name="result_effort_1_10",
            ),
        ]

    def __str__(self):
        return f"{self.workout} → {self.get_status_display()}"
