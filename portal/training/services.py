"""
Plan workflows (brief §4). Views call these; they never build plans themselves.

generate_draft: run the engine, then save the whole draft in ONE transaction. If anything fails, nothing is
saved (no half-made plans). Existing plans and results are never touched: a new draft is always a new plan.
"""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.models import ClientProfile
from .engines import GENERATORS, PlanRequest
from .models import PlanType, PlanWeek, ScheduledWorkout, TrainingPlan


def generate_draft(coach, client: ClientProfile, request: PlanRequest, today=None) -> TrainingPlan:
    if not (coach.is_authenticated and coach.is_active and coach.is_coach and client.coach_id == coach.id):
        raise PermissionDenied("Only this client's coach can generate their plans.")
    request.validate(today=today)
    generator = GENERATORS.get(request.plan_type)
    if generator is None:
        raise ValidationError({"plan_type": "This plan type can't be generated yet."})

    # Pure engine work happens before the transaction: a crash here touches nothing.
    version, engine_kwargs, plan_data = generator(request)

    label = PlanType(request.plan_type).label
    title = f"{label}: {request.race_name}" if request.race_name else f"{label} Plan"
    with transaction.atomic():
        plan = TrainingPlan.objects.create(
            client=client,
            title=title[:150],
            plan_type=request.plan_type,
            status=TrainingPlan.Status.DRAFT,
            start_date=request.start_date,
            end_date=request.end_date,
            race_name=request.race_name,
            race_date=request.race_date,
            race_distance_m=next(
                (w["distance_m"] for wk in plan_data["weeks"] for w in wk["workouts"] if w["kind"] == "race"), None
            ),
            created_by=coach,
            generator_version=version,
            input_snapshot={
                "request": request.snapshot(),
                "engine_kwargs": engine_kwargs,
                "peak_miles": plan_data.get("peak_miles"),
                "generated_at": timezone.now().isoformat(),
            },
        )
        for wk in plan_data["weeks"]:
            week = PlanWeek.objects.create(
                plan=plan, number=wk["number"], start_date=wk["start_date"], phase=wk["phase"],
                target_distance_m=wk["target_distance_m"], warnings=wk["warnings"],
            )
            for order_in_day, w in enumerate(wk["workouts"]):
                ScheduledWorkout.objects.create(
                    week=week,
                    date=w["date"],
                    order=sum(1 for x in wk["workouts"][:order_in_day] if x["date"] == w["date"]),
                    workout_type=w["kind"],
                    title=w["title"][:120],
                    prescription=w["prescription"],
                    target_distance_m=w["distance_m"],
                )
    return plan
