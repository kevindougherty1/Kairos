from flask import Flask, render_template, request, jsonify
from engineV3 import build_plan as build_marathon_plan
from half_marathon_engine_main_4plus_v5_7 import build_plan as build_hm_plan
from strength_engine import build_strength_plan

app = Flask(__name__)


def _build_strength(data, running_plan, experience):
    """Build the strength plan from request data, or None if not requested.

    Must run on the raw running plan (before schedules are flattened to
    label strings) because the strength engine reads the weekly schedules.
    """
    if not data.get("include_strength"):
        return None, None

    preferences = {}
    for key, pref in [
        ("strength_scheduling_style", "scheduling_style"),
        ("strength_recovery", "recovery"),
        ("strength_emphasis", "emphasis"),
    ]:
        value = data.get(key)
        if value and value != "auto":
            preferences[pref] = value

    pattern_equipment = {
        pattern: eq
        for pattern, eq in (data.get("strength_pattern_equipment") or {}).items()
        if eq
    }

    region_reps = {
        region: choice
        for region, choice in (data.get("strength_rep_ranges") or {}).items()
        if choice and choice != "auto"
    }

    try:
        strength = build_strength_plan(
            running_plan,
            experience,
            split=data.get("strength_split", "full_body"),
            frequency=int(data.get("strength_frequency", 3)),
            equipment=data.get("strength_equipment", "dumbbell"),
            preferences=preferences,
            overrides=data.get("lift_overrides") or {},
            pattern_equipment=pattern_equipment,
            region_reps=region_reps,
        )
        return strength, None
    except ValueError as e:
        return None, str(e)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/generate-plan", methods=["POST"])
def generate_plan():
    data = request.get_json()

    race_type = data.get("race_type", "marathon")
    experience = data.get("experience")
    current_mileage = int(data.get("current_mileage"))
    longest_run = int(data.get("longest_run"))
    runs_per_week = int(data.get("runs_per_week"))
    weeks = int(data.get("weeks"))

    if race_type == "half_marathon":
        preferences = {
            "long_run_day": data.get("long_run_day", "Sat"),
            "quality_day": data.get("speed_day", "Tue"),
            "unavailable_days": data.get("unavailable_days", []),
            "preferred_rest_days": data.get("preferred_rest_days", []),
        }
        peak, plan = build_hm_plan(
            experience=experience,
            current_mileage=current_mileage,
            recent_longest_run=longest_run,
            runs_per_week=runs_per_week,
            weeks=weeks,
            preferences=preferences,
        )
        strength, strength_error = _build_strength(data, plan, experience)
        for week in plan:
            week["schedule"] = {day: _hm_label(item) for day, item in week["schedule"].items()}
        return jsonify({
            "race_type": "half_marathon", "peak": peak, "plan": plan,
            "strength": strength, "strength_error": strength_error,
        })

    else:
        preferences = {
            "long_run_day": data.get("long_run_day"),
            "speed_day": data.get("speed_day"),
            "unavailable_days": data.get("unavailable_days", []),
            "preferred_rest_days": data.get("preferred_rest_days", []),
        }
        plan = build_marathon_plan(
            experience=experience,
            current_mileage=current_mileage,
            longest_run=longest_run,
            runs_per_week=runs_per_week,
            weeks=weeks,
            preferences=preferences,
        )
        strength, strength_error = _build_strength(data, plan, experience)
        return jsonify({
            "race_type": "marathon", "plan": plan,
            "strength": strength, "strength_error": strength_error,
        })


def _hm_label(item):
    if item["name"] == "Rest":
        return "Rest"
    if item["miles"]:
        return f"{item['name']} · {item['miles']}mi"
    return item["name"]


if __name__ == "__main__":
    app.run(debug=True)