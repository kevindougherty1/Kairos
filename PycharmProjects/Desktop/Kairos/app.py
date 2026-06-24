from flask import Flask, render_template, request, jsonify
from engineV3 import build_plan as build_marathon_plan
from half_marathon_engine_main_4plus_v5_7 import build_plan as build_hm_plan

app = Flask(__name__)


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
        for week in plan:
            week["schedule"] = {day: _hm_label(item) for day, item in week["schedule"].items()}
        return jsonify({"race_type": "half_marathon", "peak": peak, "plan": plan})

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
        return jsonify({"race_type": "marathon", "plan": plan})


def _hm_label(item):
    if item["name"] == "Rest":
        return "Rest"
    if item["miles"]:
        return f"{item['name']} · {item['miles']}mi"
    return item["name"]


if __name__ == "__main__":
    app.run(debug=True)