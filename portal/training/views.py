from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from . import access
from .forms import WorkoutResultForm
from .models import ScheduledWorkout, TrainingPlan, WorkoutResult


def role_required(role):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(request, *args, **kwargs):
            if request.user.role != role:
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return wrapped
    return decorator


def _units(user):
    profile = getattr(user, "client_profile", None)
    return profile.preferred_units if profile else "mi"


@login_required
def dashboard(request):
    """Where everyone lands after logging in."""
    if request.user.is_coach:
        return redirect("coach_home")
    return redirect("client_home")


@role_required("coach")
def coach_home(request):
    clients = access.clients_for(request.user).prefetch_related(
        Prefetch("plans", queryset=TrainingPlan.objects.order_by("-start_date"))
    )
    return render(request, "training/coach_home.html", {"clients": clients})


@role_required("client")
def client_home(request):
    plans = access.plans_for(request.user)
    current = plans.filter(status=TrainingPlan.Status.PUBLISHED).first()
    upcoming = []
    if current:
        upcoming = (
            access.workouts_for(request.user)
            .filter(week__plan=current, date__gte=timezone.localdate())
            .select_related("result")[:7]
        )
    past_plans = plans.filter(status=TrainingPlan.Status.ARCHIVED)
    return render(request, "training/client_home.html", {
        "current": current, "upcoming": upcoming, "past_plans": past_plans, "units": _units(request.user),
    })


@login_required
def plan_detail(request, pk):
    plan = get_object_or_404(access.plans_for(request.user).select_related("client__user"), pk=pk)
    weeks = plan.weeks.prefetch_related(
        Prefetch("workouts", queryset=ScheduledWorkout.objects.select_related("result"))
    )
    units = plan.client.preferred_units
    return render(request, "training/plan_detail.html", {"plan": plan, "weeks": weeks, "units": units})


@login_required
def workout_detail(request, pk):
    workout = get_object_or_404(access.workouts_for(request.user).select_related("week__plan__client__user"), pk=pk)
    result = WorkoutResult.objects.filter(workout=workout).first()
    can_log = access.can_log_result(request.user, workout)
    units = workout.week.plan.client.preferred_units

    if request.method == "POST":
        if not can_log:
            raise PermissionDenied
        form = WorkoutResultForm(request.POST, instance=result, units=units)
        if form.is_valid():
            saved = form.save(commit=False)
            saved.workout = workout  # set by the server, never from the request
            saved.prescription_version = workout.version
            saved.save()
            messages.success(request, "Result saved.")
            return redirect("workout_detail", pk=workout.pk)
    else:
        form = WorkoutResultForm(instance=result, units=units) if can_log else None

    return render(request, "training/workout_detail.html", {
        "workout": workout, "result": result, "form": form, "units": units,
    })
