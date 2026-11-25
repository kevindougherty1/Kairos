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
                    suggestion=w.get("suggestion", ""),
                    engine_detail=w.get("engine_detail", "")[:120],
                    target_distance_m=w["distance_m"],
                )
    return plan


class PlanActionError(Exception):
    """A plan action that isn't allowed, with a message the coach can act on."""


def trash_plan(coach, plan: TrainingPlan) -> None:
    if plan.client.coach_id != coach.id:
        raise PermissionDenied
    if plan.status == TrainingPlan.Status.PUBLISHED:
        raise PlanActionError(
            "The live plan can’t go in the Trash; your client is using it. Publish a new plan first (it archives this one)."
        )
    if plan.is_trashed:
        return
    plan.trashed_at, plan.trashed_by = timezone.now(), coach
    plan.save(update_fields=["trashed_at", "trashed_by", "updated_at"])


def restore_plan(coach, plan: TrainingPlan) -> None:
    if plan.client.coach_id != coach.id:
        raise PermissionDenied
    plan.trashed_at, plan.trashed_by = None, None
    plan.save(update_fields=["trashed_at", "trashed_by", "updated_at"])


def logged_result_count(plan: TrainingPlan) -> int:
    from .models import WorkoutResult

    return WorkoutResult.objects.filter(workout__week__plan=plan).count()


def delete_plan_forever(coach, plan: TrainingPlan) -> None:
    """Only from the Trash, and never a plan with logged runs (client history is kept, brief §4.6)."""
    if plan.client.coach_id != coach.id:
        raise PermissionDenied
    if not plan.is_trashed:
        raise PlanActionError("Move the plan to the Trash first.")
    runs = logged_result_count(plan)
    if runs:
        raise PlanActionError(
            f"Your client logged {runs} run{'s' if runs != 1 else ''} on this plan, so it stays in the Trash to keep "
            "their history. It’s hidden everywhere else."
        )
    with transaction.atomic():
        plan.delete()  # weeks and workouts go with it



def update_prescription(coach, workout, **changes) -> bool:
    """Coach edits what the client will see. On a live (published) plan the old version is kept as a
    PrescriptionRevision and `version` goes up, so results logged earlier stay understandable (brief §6).
    Returns True if anything changed."""
    from .models import PrescriptionRevision, ScheduledWorkout

    plan = workout.week.plan
    if plan.client.coach_id != coach.id:
        raise PermissionDenied
    if plan.is_trashed or plan.status == TrainingPlan.Status.ARCHIVED:
        raise PlanActionError("This plan is archived or in the Trash, so its workouts can’t be changed.")
    allowed = set(ScheduledWorkout.PRESCRIPTION_FIELDS)
    unknown = set(changes) - allowed
    if unknown:
        raise ValueError(f"Not editable here: {', '.join(sorted(unknown))}")
    before = workout.prescription_snapshot()
    after = {**before, **changes}
    if after == before:
        return False
    with transaction.atomic():
        if plan.status == TrainingPlan.Status.PUBLISHED:
            PrescriptionRevision.objects.create(
                workout=workout, version=workout.version, snapshot=before, changed_by=coach
            )
            workout.version += 1
        for field_name, value in changes.items():
            setattr(workout, field_name, value)
        workout.save()
    return True
