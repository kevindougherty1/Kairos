"""
Who can see what: the single source of truth for ownership checks. Every view (and the API later)
starts from these querysets instead of `Model.objects`, so a missing check shows up as "not found",
never as someone else's data.

- Coach:  only their own clients, and all of those clients' plans (drafts included).
- Client: only their own plans that have been published (current or archived), never drafts.
- Nobody sees a plan in the Trash except its coach, on the Trash page (trashed_plans_for).
"""

from accounts.models import ClientProfile
from .models import ScheduledWorkout, TrainingPlan, WorkoutResult


def _active(user):
    return user is not None and user.is_authenticated and user.is_active


def clients_for(user):
    if _active(user) and user.is_coach:
        return ClientProfile.objects.filter(coach=user).select_related("user")
    return ClientProfile.objects.none()


def plans_for(user):
    if not _active(user):
        return TrainingPlan.objects.none()
    if user.is_coach:
        return TrainingPlan.objects.filter(client__coach=user, trashed_at__isnull=True)
    if user.is_client:
        return TrainingPlan.objects.filter(
            client__user=user,
            trashed_at__isnull=True,
            status__in=[TrainingPlan.Status.PUBLISHED, TrainingPlan.Status.ARCHIVED],
            published_at__isnull=False,
        )
    return TrainingPlan.objects.none()


def trashed_plans_for(user):
    if _active(user) and user.is_coach:
        return TrainingPlan.objects.filter(client__coach=user, trashed_at__isnull=False)
    return TrainingPlan.objects.none()


def workouts_for(user):
    return ScheduledWorkout.objects.filter(week__plan__in=plans_for(user)).select_related("week__plan")


def results_for(user):
    return WorkoutResult.objects.filter(workout__in=workouts_for(user))


def can_log_result(user, workout):
    """Only the client who owns the workout, and only while its plan is the live (published) one."""
    return (
        _active(user)
        and user.is_client
        and workout.week.plan.client.user_id == user.id
        and workout.week.plan.status == TrainingPlan.Status.PUBLISHED
    )
