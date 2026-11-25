from datetime import date, timedelta
from functools import wraps
from zoneinfo import ZoneInfo

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Prefetch
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
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
        Prefetch("plans", queryset=TrainingPlan.objects.filter(trashed_at__isnull=True).order_by("-start_date"))
    )
    trash_count = access.trashed_plans_for(request.user).count()
    return render(request, "training/coach_home.html", {"clients": clients, "trash_count": trash_count, "nav": "home"})


def _back(request, fallback="coach_home"):
    target = request.POST.get("next", "")
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}):
        return redirect(target)
    return redirect(fallback)


@require_POST
@role_required("coach")
def plan_trash(request, pk):
    plan = get_object_or_404(access.plans_for(request.user).select_related("client"), pk=pk)
    try:
        services.trash_plan(request.user, plan)
    except services.PlanActionError as exc:
        messages.error(request, str(exc))
        return redirect("plan_detail", pk=plan.pk)
    messages.success(request, f"Moved “{plan.title}” to the Trash.", extra_tags=f"undo plan-{plan.pk}")
    return _back(request)


@require_POST
@role_required("coach")
def plan_restore(request, pk):
    plan = get_object_or_404(access.trashed_plans_for(request.user).select_related("client"), pk=pk)
    services.restore_plan(request.user, plan)
    messages.success(request, f"Restored “{plan.title}”.")
    return _back(request)


@role_required("coach")
def coach_trash(request):
    plans = access.trashed_plans_for(request.user).select_related("client__user").annotate(
        logged=Count("weeks__workouts__result")
    ).order_by("-trashed_at")
    return render(request, "training/trash.html", {"plans": plans})


@role_required("coach")
def plan_delete(request, pk):
    """Delete forever: a confirmation page (GET), then the delete (POST). Only from the Trash."""
    plan = get_object_or_404(access.trashed_plans_for(request.user).select_related("client__user"), pk=pk)
    logged = services.logged_result_count(plan)
    if request.method == "POST":
        try:
            services.delete_plan_forever(request.user, plan)
        except services.PlanActionError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, f"Deleted “{plan.title}” forever.")
        return redirect("coach_trash")
    return render(request, "training/plan_delete.html", {"plan": plan, "logged": logged})


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
