from datetime import date, timedelta
from functools import wraps
from zoneinfo import ZoneInfo

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from django.core.exceptions import ValidationError

from . import access, services
from .engines import PlanRequest
from .forms import GeneratePlanForm, WorkoutResultForm
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
    return render(request, "training/coach_home.html", {"clients": clients, "nav": "home"})


def client_today(profile):
    """Today's date where the client lives (ClientProfile.timezone), not on the server."""
    tz = ZoneInfo(profile.timezone) if profile else timezone.get_current_timezone()
    return timezone.now().astimezone(tz).date()


def _monday(day):
    return day - timedelta(days=day.weekday())


@role_required("client")
def client_home(request):
    """This Week: the client's current plan week, Mon–Sun, rest days included.
    ?week=YYYY-MM-DD (any day of the week) shows another week of the same plan."""
    profile = getattr(request.user, "client_profile", None)
    plans = access.plans_for(request.user)
    current = plans.filter(status=TrainingPlan.Status.PUBLISHED).first()
    past_plans = plans.filter(status=TrainingPlan.Status.ARCHIVED)
    context = {"current": current, "past_plans": past_plans, "units": _units(request.user), "nav": "home"}
    if not current:
        return render(request, "training/client_home.html", context)

    today = client_today(profile)
    this_monday = _monday(today)
    first_monday, last_monday = _monday(current.start_date), _monday(current.end_date)
    try:
        monday = _monday(date.fromisoformat(request.GET.get("week", "")))
    except ValueError:
        monday = this_monday
    monday = min(max(monday, first_monday), last_monday)  # stay inside the plan
    sunday = monday + timedelta(days=6)

    workouts = list(
        access.workouts_for(request.user)
        .filter(week__plan=current, date__range=(monday, sunday))
        .select_related("result")
    )
    days = []
    for offset in range(7):
        day = monday + timedelta(days=offset)
        days.append({"date": day, "is_today": day == today, "workouts": [w for w in workouts if w.date == day]})

    results = [w.result for w in workouts if hasattr(w, "result")]
    next_up = (
        access.workouts_for(request.user)
        .filter(week__plan=current, date__gte=today, result__isnull=True)
        .order_by("date", "order")
        .first()
    )
    context.update({
        "today": today,
        "monday": monday,
        "is_this_week": monday == this_monday,
        "plan_week": current.weeks.filter(start_date=monday).first(),
        "days": days,
        "next_up": next_up,
        "planned_m": sum(w.target_distance_m or 0 for w in workouts),
        "logged_m": sum(r.actual_distance_m or 0 for r in results),
        "logged_count": len(results),
        "workout_count": len(workouts),
        "prev_week": monday - timedelta(days=7) if monday > first_monday else None,
        "next_week": monday + timedelta(days=7) if monday < last_monday else None,
    })
    return render(request, "training/client_home.html", context)


@role_required("coach")
def generate_plan(request, client_id):
    """Coach: run the engine for one of their clients and save the result as a draft."""
    client = get_object_or_404(access.clients_for(request.user), pk=client_id)
    if request.method == "POST":
        form = GeneratePlanForm(request.POST)
        if form.is_valid():
            plan_request = PlanRequest(**form.cleaned_data)
            try:
                plan = services.generate_draft(request.user, client, plan_request, today=client_today(client))
            except ValidationError as exc:
                for field_name, errors in exc.message_dict.items():
                    form.add_error(field_name if field_name in form.fields else None, errors)
            else:
                messages.success(request, "Draft created. Review the weeks below; your client can’t see it yet.")
                return redirect("plan_detail", pk=plan.pk)
        form.focus_first_error()
    else:
        form = GeneratePlanForm(initial=GeneratePlanForm.initial_from(client))
    return render(request, "training/generate_plan.html", {"client": client, "form": form})


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
        form.focus_first_error()
    else:
        form = WorkoutResultForm(instance=result, units=units) if can_log else None

    return render(request, "training/workout_detail.html", {
        "workout": workout, "result": result, "form": form, "units": units,
    })
