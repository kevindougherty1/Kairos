from flask import Flask, render_template, request, jsonify
from engineV3 import build_plan

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/generate-plan", methods=["POST"])
def generate_plan():
    data = request.get_json()

    experience = data.get("experience")
    current_mileage = int(data.get("current_mileage"))
    longest_run = int(data.get("longest_run"))
    runs_per_week = int(data.get("runs_per_week"))
    weeks = int(data.get("weeks"))

    preferences = {
        "long_run_day": data.get("long_run_day"),
        "speed_day": data.get("speed_day"),
        "unavailable_days": data.get("unavailable_days", []),
        "preferred_rest_days": data.get("preferred_rest_days", []),
        "hard_day_style": data.get("hard_day_style", "spread")
    }

    plan = build_plan(
        experience=experience,
        current_mileage=current_mileage,
        longest_run=longest_run,
        runs_per_week=runs_per_week,
        weeks=weeks,
        preferences=preferences
    )

    return jsonify(plan)


if __name__ == "__main__":
    app.run(debug=True)