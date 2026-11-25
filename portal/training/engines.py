"""
Engine adapter: validated portal inputs → engine call → one normalized plan shape (portal/ENGINES.md).

The engines at the repo root are imported unchanged. This module is pure (no database): it validates,
calls the engine, and returns plain data; training/services.py saves it.

Decisions applied (PORTAL_SESSION_LOG.md, 2026-11-21):
- Plan length: half marathon 8–20 weeks, marathon 12–24.
- The plan is built backward from the client's real race date; the race lands on that date.
- Race-week total = the engine's shakeouts + the race distance.
"""

import copy
import hashlib
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError

from accounts.models import Experience, RaceDistance, Weekday
from core.units import miles_to_m

from .models import PlanType, WorkoutType

DAYS = Weekday.values  # ["Mon", ..., "Sun"], the engines' own names
WEEK_RANGE = {PlanType.HALF_MARATHON: (8, 20), PlanType.MARATHON: (12, 24)}
RUNS_PER_WEEK = (4, 6)
HM_FILE = "half_marathon_engine_main_4plus_v5_7.py"

# Engine workout name → (portal kind, title the CLIENT sees, short label the COACH sees as the engine's pick).
# The one place to rename engine terms. Decision 2026-11-25: clients see "Speed Session" for all quality work and
# "Easy Run + Strides" for strides days; the engine's specific pick is a coach-only suggestion.
HM_WORKOUTS = {
    "Easy": (WorkoutType.EASY, "Easy Run", ""),
    "Long Run": (WorkoutType.LONG_RUN, "Long Run", "Long Run"),
    "Threshold Session": (WorkoutType.THRESHOLD, "Speed Session", "Threshold"),
    "HMP Session": (WorkoutType.RACE_PACE, "Speed Session", "Half Marathon Pace"),
    "Hill Strength": (WorkoutType.HILLS, "Speed Session", "Hills"),
    "Speed Support": (WorkoutType.SPEED, "Speed Session", "Speed Support"),
    "Economy Support": (WorkoutType.ECONOMY, "Easy Run + Strides", "Strides"),
    "Shakeout": (WorkoutType.SHAKEOUT, "Shakeout Run", ""),
    "Half Marathon Race": (WorkoutType.RACE, "Half Marathon Race", ""),
}


@dataclass
class PlanRequest:
    """What the coach asks for. Field names are the portal's; to_engine_kwargs() maps them to the engine's."""

    plan_type: str
    experience: str
    current_mileage: int
    longest_run: int
    runs_per_week: int
    weeks: int
    race_date: date
    race_name: str = ""
    long_run_day: str = "Sat"
    quality_day: str = "Tue"
    unavailable_days: list = field(default_factory=list)
    preferred_rest_days: list = field(default_factory=list)

    def validate(self, today=None):
        errors = {}
        if self.plan_type not in WEEK_RANGE:
            errors["plan_type"] = "Only half marathon and marathon plans can be generated so far."
        else:
            lo, hi = WEEK_RANGE[self.plan_type]
            if not lo <= self.weeks <= hi:
                errors["weeks"] = f"Choose {lo} to {hi} weeks for this plan type."
        if self.experience not in Experience.values:
            errors["experience"] = "Choose beginner, intermediate or advanced."
        if not RUNS_PER_WEEK[0] <= self.runs_per_week <= RUNS_PER_WEEK[1]:
            errors["runs_per_week"] = "The engines plan 4 to 6 runs a week."
        if not 0 <= self.current_mileage <= 150:
            errors["current_mileage"] = "Enter current weekly miles between 0 and 150."
        if not 0 <= self.longest_run <= 40:
            errors["longest_run"] = "Enter the longest recent run in miles, 0 to 40."
        days = [self.long_run_day, self.quality_day, *self.unavailable_days, *self.preferred_rest_days]
        if any(d not in DAYS for d in days):
            errors["long_run_day"] = "Use day names Mon to Sun."
        if today and "weeks" not in errors and self.start_date < today - timedelta(days=today.weekday()):
            weeks_left = (_monday(self.race_date) - _monday(today)).days // 7 + 1
            errors["weeks"] = (f"The race is only {max(weeks_left, 0)} week(s) away, so a {self.weeks}-week plan would "
                               "start in the past. Pick fewer weeks or a later race.")
        if errors:
            raise ValidationError(errors)

    @property
    def start_date(self):
        """Monday of week 1: the plan is counted backward from the race week."""
        return _monday(self.race_date) - timedelta(weeks=self.weeks - 1)

    @property
    def end_date(self):
        return _monday(self.race_date) + timedelta(days=6)

    def to_engine_kwargs(self):
        prefs = {
            "long_run_day": self.long_run_day,
            "unavailable_days": list(self.unavailable_days),
            "preferred_rest_days": list(self.preferred_rest_days),
        }
        if self.plan_type == PlanType.HALF_MARATHON:
            prefs["quality_day"] = self.quality_day
            return {"experience": self.experience, "current_mileage": self.current_mileage,
                    "recent_longest_run": self.longest_run, "runs_per_week": self.runs_per_week,
                    "weeks": self.weeks, "preferences": prefs}
        prefs["speed_day"] = self.quality_day
        return {"experience": self.experience, "current_mileage": self.current_mileage,
                "longest_run": self.longest_run, "runs_per_week": self.runs_per_week,
                "weeks": self.weeks, "preferences": prefs}

    def snapshot(self):
        data = asdict(self)
        data["race_date"] = self.race_date.isoformat()
        return data


def _monday(day):
    return day - timedelta(days=day.weekday())


def generator_version(filename):
    """'<engine file>@<sha256[:12]>': the engines carry no version constant, so the file hash is the version."""
    digest = hashlib.sha256((settings.REPO_ROOT / filename).read_bytes()).hexdigest()[:12]
    return f"{Path(filename).stem}@{digest}"


def _hm_prescription(name, style):
    from half_marathon_engine_main_4plus_v5_7 import WORKOUT_GLOSSARY

    category = "Long Run" if name == "Long Run" else name
    entry = WORKOUT_GLOSSARY.get(category)
    if not entry:
        return ""
    lines = [entry["purpose"], f"Effort: {entry['effort_cue']}"]
    examples = entry["styles"].get(style or "", [])
    if style:
        lines.append(f"Suggested style: {style}" + (" (pick one):" if examples else ""))
        lines += [f"• {e}" for e in examples]
    return "\n".join(lines)


def generate_half_marathon(request: PlanRequest):
    """Run the HM engine and return (generator_version, engine_kwargs, normalized_plan)."""
    from half_marathon_engine_main_4plus_v5_7 import build_plan

    kwargs = request.to_engine_kwargs()
    peak, plan = build_plan(**copy.deepcopy(kwargs))
    weeks = []
    start = request.start_date
    race_weekday = DAYS[request.race_date.weekday()]

    for week in plan:
        number = week["week"]
        week_start = start + timedelta(weeks=number - 1)
        is_race_week = week["phase"] == "Race"
        warnings = list(week.get("warnings", []))
        if number == 1:
            warnings = list(week.get("plan_warnings", [])) + warnings
        workouts = []
        for day in DAYS:
            item = week["schedule"][day]
            if item["name"] == "Rest":
                continue
            if item["name"] not in HM_WORKOUTS:
                raise ValueError(f"Unknown engine workout {item['name']!r}; add it to HM_WORKOUTS.")
            kind, title, engine_label = HM_WORKOUTS[item["name"]]
            style = item.get("style")
            weekday = day
            if kind == WorkoutType.RACE:
                weekday = race_weekday  # decision: the race lands on the real race date
            workouts.append({
                "weekday": weekday,
                "kind": kind,
                "title": request.race_name or title if kind == WorkoutType.RACE else title,
                "distance_m": RaceDistance.HALF_MARATHON if kind == WorkoutType.RACE else miles_to_m(item["miles"] or 0) or None,
                "prescription": "",  # written by the coach; clients see only this
                "suggestion": _hm_prescription(item["name"], style),
                "engine_detail": f"{engine_label} · {style}" if engine_label and style else engine_label,
                "engine_label": item["name"],
            })
        if is_race_week:
            # Any run the engine put on the real race day gives way to the race.
            clash = [w for w in workouts if w["weekday"] == race_weekday and w["kind"] != WorkoutType.RACE]
            for w in clash:
                workouts.remove(w)
                warnings.append(f"{w['title']} on {w['weekday']} was dropped: that's race day.")
        workouts.sort(key=lambda w: DAYS.index(w["weekday"]))
        target_m = miles_to_m(week["mileage"])
        if is_race_week:
            target_m = sum(w["distance_m"] or 0 for w in workouts)  # shakeouts + the race (decision 2026-11-21)
        weeks.append({
            "number": number,
            "start_date": week_start,
            "phase": week["phase"],
            "target_distance_m": target_m,
            "warnings": warnings,
            "workouts": [{**w, "date": week_start + timedelta(days=DAYS.index(w["weekday"]))} for w in workouts],
        })
    return generator_version(HM_FILE), kwargs, {"peak_miles": peak, "weeks": weeks}


GENERATORS = {PlanType.HALF_MARATHON: generate_half_marathon}
