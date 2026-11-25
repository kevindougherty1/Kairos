"""Decision 2026-11-25: clients see "Speed Session" / "Easy Run + Strides"; the engine's pick and guidance are
coach-only suggestions. Converts workouts saved before this change (generated drafts + demo fixtures)."""

import re

from django.db import migrations

QUALITY = {"threshold", "tempo", "vo2", "race_pace", "hills", "speed"}
ENGINE_TITLES = {"Threshold Session": "Threshold", "HMP Session": "Half Marathon Pace",
                 "Hill Strength": "Hills", "Speed Support": "Speed Support", "Economy Support": "Strides",
                 "Long Run": "Long Run"}
STYLE = re.compile(r"^Suggested style: (.+?)(?: \(pick one\):)?$", re.M)


def forwards(apps, schema_editor):
    Workout = apps.get_model("training", "ScheduledWorkout")
    for w in Workout.objects.select_related("week__plan"):
        generated = bool(w.week.plan.generator_version)
        old_title = w.title
        changed = []
        if generated and w.prescription and not w.suggestion:
            w.suggestion, w.prescription = w.prescription, ""
            changed += ["suggestion", "prescription"]
        if generated and not w.engine_detail and old_title in ENGINE_TITLES:
            style = STYLE.search(w.suggestion or "")
            w.engine_detail = ENGINE_TITLES[old_title] + (f" · {style.group(1)}" if style else "")
            changed.append("engine_detail")
        if w.workout_type in QUALITY and old_title in ENGINE_TITLES:
            w.title = "Speed Session"
            changed.append("title")
        elif w.workout_type == "economy" and old_title == "Economy Support":
            w.title = "Easy Run + Strides"
            changed.append("title")
        if changed:
            w.save(update_fields=changed)


class Migration(migrations.Migration):
    dependencies = [("training", "0003_workout_engine_suggestion")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
