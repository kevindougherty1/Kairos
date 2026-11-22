from django.contrib import admin

from .models import PlanWeek, PrescriptionRevision, ScheduledWorkout, TrainingPlan, WorkoutResult


class PlanWeekInline(admin.TabularInline):
    model = PlanWeek
    extra = 0
    fields = ("number", "start_date", "phase", "target_distance_m", "warnings")
    show_change_link = True


@admin.register(TrainingPlan)
class TrainingPlanAdmin(admin.ModelAdmin):
    list_display = ("title", "client", "plan_type", "status", "start_date", "end_date", "is_fixture")
    list_filter = ("status", "plan_type", "is_fixture")
    search_fields = ("title", "client__user__username", "race_name")
    date_hierarchy = "start_date"
    readonly_fields = ("generator_version", "input_snapshot", "published_at", "created_at", "updated_at")
    inlines = [PlanWeekInline]


class ScheduledWorkoutInline(admin.TabularInline):
    model = ScheduledWorkout
    extra = 0
    fields = ("date", "order", "workout_type", "title", "target_distance_m", "target_duration_s", "version")
    readonly_fields = ("version",)
    show_change_link = True


@admin.register(PlanWeek)
class PlanWeekAdmin(admin.ModelAdmin):
    list_display = ("__str__", "plan", "start_date", "phase", "target_distance_m")
    list_filter = ("plan__status",)
    inlines = [ScheduledWorkoutInline]


@admin.register(ScheduledWorkout)
class ScheduledWorkoutAdmin(admin.ModelAdmin):
    list_display = ("date", "title", "workout_type", "week", "version")
    list_filter = ("workout_type", "week__plan__status")
    search_fields = ("title", "week__plan__title")
    readonly_fields = ("version", "created_at", "updated_at")


@admin.register(WorkoutResult)
class WorkoutResultAdmin(admin.ModelAdmin):
    list_display = ("workout", "status", "perceived_effort", "updated_at")
    list_filter = ("status",)
    readonly_fields = ("prescription_version", "created_at", "updated_at")


@admin.register(PrescriptionRevision)
class PrescriptionRevisionAdmin(admin.ModelAdmin):
    """Audit records are written by the app, never edited by hand."""

    list_display = ("workout", "version", "changed_by", "changed_at", "reason")
    readonly_fields = ("workout", "version", "snapshot", "changed_by", "changed_at", "reason")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
