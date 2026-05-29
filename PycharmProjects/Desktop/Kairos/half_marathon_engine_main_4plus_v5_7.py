import math

# HALF MARATHON ENGINE MAIN 4PLUS V5.7
# Refinements from V5:
# - Long-run wave logic to avoid repeated max long runs.
# - Lower advanced 5-day cap to avoid awkward 50 mpw / 5-day plans.
# - Better taper long-run decline.
# - Keeps weekly shape optimizer.
# - Keeps suggested workout styles.
# - Still intentionally lean; schedule/glossary can be merged back later.

MIN_PEAK = 18
MAX_PEAK = 60

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


# -----------------------------
# BASIC OBJECTS
# -----------------------------

def workout(category, miles, style=None):
    return {
        "category": category,
        "miles": miles,
        "suggested_style": style,
    }

# -----------------------------
# V6 PRODUCT / APP LAYER
# -----------------------------

WORKOUT_GLOSSARY = {
    "Threshold Session": {
        "purpose": "Improve sustainable speed and lactate-threshold fitness.",
        "effort_cue": "Comfortably hard and controlled.",
        "styles": {
            "Cruise Intervals": [
                "4 x 1 mile at threshold with 60-90 sec easy jog",
                "5 x 5 min at threshold with 75 sec easy jog",
                "3 x 2 km at threshold with 90 sec easy jog",
            ],
            "Tempo Blocks": [
                "3 x 10 min at threshold with 2 min easy jog",
                "2 x 15 min controlled hard with 3 min easy jog",
                "4 x 8 min at threshold with 90 sec easy jog",
            ],
            "Continuous Tempo": [
                "20 min continuous tempo",
                "25-35 min controlled tempo",
                "40 min steady tempo slightly slower than true threshold",
            ],
            "Tempo Progression": [
                "Start steady, finish near half-marathon effort",
                "10 min steady + 10 min moderate + 10 min strong",
                "Last 15-20 min gradually progressing to HMP feel",
            ],
        },
    },
    "HMP Session": {
        "purpose": "Practice goal half-marathon pace and make race rhythm feel familiar.",
        "effort_cue": "Goal half-marathon effort; strong but smooth, not a time trial.",
        "styles": {
            "HMP Blocks": [
                "2 x 2 miles at HMP with 3 min easy jog",
                "2 x 3 miles at HMP with 3 min easy jog",
                "3 x 2 miles at HMP with 2-3 min easy jog",
            ],
            "Continuous HMP": [
                "3-4 miles continuous at HMP",
                "4-6 miles continuous at HMP for advanced runners",
                "20-35 min continuous at goal race effort",
            ],
            "Progression to HMP": [
                "Easy start, finish final 15-25 min near HMP",
                "Middle miles steady, final miles at HMP feel",
                "Controlled progression ending at race rhythm",
            ],
        },
    },
    "Hill Strength": {
        "purpose": "Build running economy, mechanics, and strength without exact pace targets.",
        "effort_cue": "Strong uphill running with clean form and controlled breathing.",
        "styles": {
            "Short Hill Reps": [
                "8-10 x 30-45 sec uphill, jog down recovery",
                "10 x 45 sec strong hill effort, jog down",
                "6-8 x 60 sec uphill at controlled hard effort",
            ],
            "Long Hill Reps": [
                "5-6 x 2 min uphill at 10K effort",
                "4-5 x 3 min uphill at controlled hard effort",
                "Rolling hill run with controlled surges",
            ],
            "Hill Sprints": [
                "6-8 x 10-15 sec steep hill sprint with full recovery",
                "Add after easy run when legs feel fresh",
                "Focus on power and form, not exhaustion",
            ],
        },
    },
    "Speed Support": {
        "purpose": "Improve speed reserve, aerobic ceiling, and comfort faster than HMP.",
        "effort_cue": "Faster than HMP, but controlled. Quality reps, not a race effort.",
        "styles": {
            "VO2 Support": [
                "5 x 3 min at 5K-10K effort with equal easy recovery",
                "6 x 800m at 5K-10K effort with easy jog recovery",
                "4-6 x 1 km at 10K effort with 2 min easy jog",
            ],
            "10K Support": [
                "6 x 2 min at 10K effort with 90 sec easy",
                "5 x 4 min at 10K effort with 2 min easy",
                "4 x 1 mile around 10K effort with generous recovery",
            ],
        },
    },
    "Economy Support": {
        "purpose": "Keep turnover, coordination, and relaxed speed without adding much fatigue.",
        "effort_cue": "Fast but relaxed. Full recovery between accelerations.",
        "styles": {
            "Strides": [
                "6-10 x 20 sec relaxed-fast strides after easy miles",
                "8 x 15 sec fast-but-smooth with full recovery",
                "Easy run plus short relaxed accelerations",
            ],
            "Short Repetition Touches": [
                "6-8 x 200m relaxed-fast with full recovery",
                "10 x 30 sec quick but smooth with easy jog recovery",
                "Light turnover work after an easy run",
            ],
        },
    },
    "Long Run": {
        "purpose": "Build aerobic durability and late-race fatigue resistance.",
        "effort_cue": "Mostly easy. Quality finishes should feel controlled, not like racing.",
        "styles": {
            "Easy LR": [
                "All easy conversational running",
                "Keep effort relaxed and sustainable",
                "Use this when fatigue is high or mileage is building",
            ],
            "Steady Finish LR": [
                "Last 10-15 min steady",
                "Last 1-2 miles moderate but controlled",
                "Easy overall with a small finish progression",
            ],
            "Progression LR": [
                "Start easy, gradually progress the final third",
                "Finish near steady/HM effort without sprinting",
                "Controlled negative split long run",
            ],
            "Fast Finish LR": [
                "Last 2-4 miles steady or HMP feel",
                "Final 20-30 min controlled strong",
                "Easy first half, stronger second half",
            ],
            "Taper LR": [
                "Reduced long run",
                "Keep effort relaxed",
                "No hero workouts during taper",
            ],
        },
    },
}


def day_index(day):
    return DAYS.index(day)


def offset_day(day, offset):
    return DAYS[(day_index(day) + offset) % 7]


def schedule_item(name, miles=0, style=None):
    return {"name": name, "miles": miles, "style": style}


def schedule_label(item, show_styles=False):
    name = item["name"]
    miles = item.get("miles", 0)
    style = item.get("style")

    if name == "Rest":
        return "Rest"

    if show_styles and style:
        return f"{name} ({miles}) [{style}]"

    if miles:
        return f"{name} ({miles})"

    return name


def is_available(day, schedule, unavailable_days):
    return schedule[day]["name"] == "Rest" and day not in unavailable_days


def choose_best_day(candidates, schedule, unavailable_days, preferred_rest_days):
    for day in candidates:
        if schedule[day]["name"] == "Rest" and day not in unavailable_days and day not in preferred_rest_days:
            return day

    for day in candidates:
        if schedule[day]["name"] == "Rest" and day not in unavailable_days:
            return day

    return None


def secondary_candidates(primary_day, long_run_day):
    return [
        offset_day(primary_day, 2),
        offset_day(primary_day, 3),
        offset_day(long_run_day, -3),
        offset_day(long_run_day, -4),
        offset_day(primary_day, -2),
    ]


def build_week_schedule(sessions, phase, preferences):
    schedule = {day: schedule_item("Rest") for day in DAYS}
    warnings = []

    long_run_day = preferences.get("long_run_day", "Sat")
    primary_day = preferences.get("quality_day", preferences.get("speed_day", "Tue"))
    unavailable_days = preferences.get("unavailable_days", [])
    preferred_rest_days = preferences.get("preferred_rest_days", [])
    hard_day_style = preferences.get("hard_day_style", "spread")

    z2_runs = sessions["z2_runs"][:]

    if phase == "Race":
        if long_run_day in unavailable_days:
            warnings.append(f"Race day {long_run_day} is unavailable.")
        else:
            schedule[long_run_day] = schedule_item("Half Marathon Race")

        for day, miles in zip([offset_day(long_run_day, -5), offset_day(long_run_day, -3)], [3, 3]):
            if day not in unavailable_days and schedule[day]["name"] == "Rest":
                schedule[day] = schedule_item("Shakeout", miles)

        return {"schedule": schedule, "warnings": warnings}

    if long_run_day in unavailable_days:
        warnings.append(f"Long run day {long_run_day} is unavailable.")
    else:
        schedule[long_run_day] = schedule_item("Long Run", sessions["lr"], sessions["lr_style"])

    primary = sessions["primary"]
    if primary and primary["miles"] > 0:
        if primary_day == long_run_day:
            warnings.append("Primary quality day conflicts with long run day.")
        elif primary_day in unavailable_days:
            warnings.append(f"Primary quality day {primary_day} is unavailable.")
        elif schedule[primary_day]["name"] != "Rest":
            warnings.append(f"Primary quality day {primary_day} is already occupied.")
        else:
            schedule[primary_day] = schedule_item(primary["category"], primary["miles"], primary["suggested_style"])

    secondary = sessions["secondary"]
    if secondary and secondary["miles"] > 0:
        candidates = secondary_candidates(primary_day, long_run_day)

        if hard_day_style == "spread":
            candidates = [day for day in candidates if day not in [primary_day, long_run_day]]

        chosen_day = choose_best_day(candidates, schedule, unavailable_days, preferred_rest_days)

        if chosen_day:
            schedule[chosen_day] = schedule_item(secondary["category"], secondary["miles"], secondary["suggested_style"])
        else:
            warnings.append("Could not place secondary workout in an ideal slot.")

    remaining_days = [
        day for day in DAYS
        if is_available(day, schedule, unavailable_days) and day not in preferred_rest_days
    ]

    for day in remaining_days:
        if z2_runs:
            schedule[day] = schedule_item("Easy", z2_runs.pop(0))

    for day in preferred_rest_days:
        if z2_runs and is_available(day, schedule, unavailable_days):
            schedule[day] = schedule_item("Easy", z2_runs.pop(0))
            warnings.append(f"Preferred rest day {day} was used for a run.")

    if z2_runs:
        warnings.append("Not all easy runs could be placed.")

    return {"schedule": schedule, "warnings": warnings}


def print_workout_glossary():
    print("\nKAIROS HALF MARATHON WORKOUT GLOSSARY\n")

    for category, data in WORKOUT_GLOSSARY.items():
        print(category)
        print(f"  Purpose: {data['purpose']}")
        print(f"  Effort Cue: {data['effort_cue']}")
        print("  Example Options:")

        for style, examples in data["styles"].items():
            print(f"    {style}:")
            for example in examples:
                print(f"      - {example}")

        print()


def validate_engine_inputs(experience, runs_per_week):
    """
    Main half marathon engine supports 4+ run days.
    3-day plans should use a separate low-frequency / finish-oriented engine later.
    """
    valid_experience = ["beginner", "intermediate", "advanced"]

    if experience not in valid_experience:
        raise ValueError(f"experience must be one of {valid_experience}")

    if runs_per_week < 4:
        raise ValueError(
            "This main half-marathon engine supports 4+ run days per week. "
            "Use a separate 3-day low-frequency engine for 3-day plans."
        )

    if runs_per_week > 7:
        raise ValueError("runs_per_week must be between 4 and 7 for this engine.")

    if runs_per_week == 7 and experience == "beginner":
        raise ValueError(
            "7-day beginner plans are not supported in the main engine. "
            "Use 4-6 days for beginner plans."
        )


# -----------------------------
# PEAK MILEAGE ENGINE
# -----------------------------

def frequency_peak_range(experience, runs_per_week):
    """
    Peak mileage range depends on experience AND run frequency.

    Supported in main engine:
    - 4-day beginner/intermediate/advanced
    - 5-day beginner/intermediate/advanced
    - 6-day beginner/intermediate/advanced
    - 7-day intermediate/advanced only
    """
    table = {
        4: {
            "beginner": (18, 28),
            # Lowered from 40 after validation showed chunky 4-day intermediate peak weeks.
            "intermediate": (28, 38),
            # Lowered from 44 after validation showed LR identity issues on 4-day advanced plans.
            "advanced": (34, 40),
        },
        5: {
            "beginner": (22, 32),
            "intermediate": (34, 42),
            # Lowered from 46 after validation showed occasional 10/9 easy runs.
            "advanced": (40, 44),
        },
        6: {
            "beginner": (28, 38),
            "intermediate": (38, 52),
            # Lowered from 60 to reduce edge-case advanced peak chunkiness.
            "advanced": (46, 58),
        },
        7: {
            "beginner": (30, 40),  # blocked by validation for now
            "intermediate": (42, 55),
            # Slightly lowered from 60 for consistency with advanced cap philosophy.
            "advanced": (50, 58),
        },
    }

    rpw = max(4, min(7, runs_per_week))
    return table[rpw][experience]


def determine_peak_mileage(experience, current_mileage, weeks, runs_per_week):
    lower, upper = frequency_peak_range(experience, runs_per_week)

    growth_weeks = max(1, weeks - 3)
    ramp_peak = round(current_mileage * (1.065 ** growth_weeks))

    peak = min(upper, ramp_peak)
    peak = max(lower, peak)
    peak = min(MAX_PEAK, max(MIN_PEAK, peak))
    # Never plan below the runner's current fitness
    peak = max(peak, min(current_mileage, MAX_PEAK))

    return peak


# -----------------------------
# PHASE ENGINE
# -----------------------------

def build_phases(weeks):
    race_weeks = 1
    taper_weeks = 2
    dev_weeks = weeks - race_weeks - taper_weeks

    base = round(dev_weeks * 0.35)
    build = round(dev_weeks * 0.42)
    specific = dev_weeks - base - build

    return (
        ["Base"] * base
        + ["Build"] * build
        + ["Specific"] * specific
        + ["Taper"] * taper_weeks
        + ["Race"] * race_weeks
    )


# -----------------------------
# WEEKLY MILEAGE CURVE
# -----------------------------

def segment(start, end, n, cutback=False):
    if n <= 0:
        return []

    vals = []
    for i in range(1, n + 1):
        progress = (i / n) ** 1.20
        vals.append(round(start + (end - start) * progress))

    if cutback and n >= 4:
        vals[-1] = round(vals[-2] * 0.86)

    return vals


def weekly_curve(peak, phases, current_mileage):
    weekly = []

    base_n = phases.count("Base")
    build_n = phases.count("Build")
    specific_n = phases.count("Specific")

    normal_base_end = round(peak * 0.82)
    if current_mileage >= normal_base_end:
        # Runner enters the plan at or above the normal base ceiling.
        # Ramp gently toward the build phase rather than trending flat or down.
        build_entry = round(peak * 0.95)
        base_end = min(current_mileage + 4, build_entry - 2)
        base_end = max(base_end, current_mileage)
    else:
        base_end = normal_base_end

    weekly += segment(
        current_mileage,
        base_end,
        base_n,
        cutback=False,
    )

    build_start = weekly[-1] if weekly else current_mileage
    weekly += segment(
        build_start,
        round(peak * 0.95),
        build_n,
        cutback=True,
    )

    specific_start = weekly[-1] if weekly else current_mileage
    weekly += segment(
        specific_start,
        peak,
        specific_n,
        cutback=False,
    )

    # Two-week taper + race week.
    weekly += [round(peak * 0.70), round(peak * 0.52), 6]

    return weekly


# -----------------------------
# LONG RUN ENGINE
# -----------------------------

def lr_cap(experience, runs_per_week):
    caps = {
        "beginner": 12,
        "intermediate": 14,
        "advanced": 16,
    }

    cap = caps[experience]

    if runs_per_week == 4:
        cap = min(cap, 12)
    if runs_per_week == 5:
        cap = min(cap, 14)  # half marathon specificity; 16 is marathon territory at 5-day frequency

    return cap


def base_long_run_target(mileage, phase, runs_per_week=5):
    # 4-day plans have fewer total runs so the long run carries a larger share
    # of weekly mileage.  Higher percentages let the LR actually build toward
    # the cap on low-volume 4-day plans (e.g. beginner 15 mpw) where the
    # standard 30-32 % formula would stall the LR at 8 miles all season.
    if runs_per_week == 4:
        pct = {"Base": 0.32, "Build": 0.38, "Specific": 0.44}.get(phase, 0.32)
    else:
        pct = {"Base": 0.30, "Build": 0.31, "Specific": 0.32}.get(phase, 0.30)

    return round(mileage * pct)


def initialize_week1_lr(target_lr, weekly_mileage, recent_longest_run):
    """recent_longest_run is a Week 1 ceiling/readiness marker, not a required floor."""
    lower_bound = max(6, round(weekly_mileage * 0.24))
    upper_bound = max(6, recent_longest_run)

    lr = min(target_lr, upper_bound)
    lr = max(lr, lower_bound)
    lr = min(lr, upper_bound)
    lr = max(6, round(lr / 2) * 2)
    return lr


def raw_long_runs(weekly, phases, experience, recent_longest_run, runs_per_week):
    """
    First pass long-run calculation.
    """
    cap = lr_cap(experience, runs_per_week)
    previous = 0
    long_runs = []

    for mileage, phase in zip(weekly, phases):
        if phase == "Race":
            long_runs.append(0)
            continue

        if phase == "Taper":
            # Placeholder. Real taper handled after LR wave logic.
            long_runs.append(0)
            continue

        target = base_long_run_target(mileage, phase, runs_per_week)

        if previous == 0:
            lr = initialize_week1_lr(target, mileage, recent_longest_run)
        else:
            lr = min(target, previous + 2)
            lr = max(lr, round(mileage * 0.25))
        lr = min(lr, cap)
        # 4-day plans use ceiling-to-even so that an odd target like 9 rounds
        # up to 10 rather than down to 8 (Python banker's rounding).  This lets
        # the LR actually progress on low-volume 4-day plans.
        if runs_per_week == 4:
            lr = max(6, math.ceil(lr / 2) * 2)
        else:
            lr = max(6, round(lr / 2) * 2)

        long_runs.append(lr)
        previous = lr

    return long_runs


def apply_long_run_wave_logic(long_runs, phases, experience, runs_per_week):
    """
    Avoid stale repetition like 14 / 14 / 14 or 16 / 16 / 16.

    Coaching idea:
    - Reaching the cap is fine.
    - Sitting at the cap for three straight weeks is less elegant.
    - Wave the first repeated cap down when possible, then finish strong.
    """
    cap = lr_cap(experience, runs_per_week)

    adjusted = long_runs[:]

    # Find non-taper development weeks.
    dev_indices = [
        i for i, phase in enumerate(phases)
        if phase in ["Base", "Build", "Specific"]
    ]

    # Prevent 3 straight cap weeks.
    for i in range(2, len(adjusted)):
        if phases[i] in ["Build", "Specific"]:
            if adjusted[i] == cap and adjusted[i - 1] == cap and adjusted[i - 2] == cap:
                # Step the middle of the three down.
                adjusted[i - 1] = max(6, cap - 2)

    # Keep final specific long run strong if available.
    specific_indices = [i for i, phase in enumerate(phases) if phase == "Specific"]
    if specific_indices:
        final_specific = specific_indices[-1]
        adjusted[final_specific] = max(adjusted[final_specific], min(cap, adjusted[final_specific]))

    return adjusted


def apply_taper_long_runs(long_runs, phases, experience, runs_per_week):
    """
    Make taper LRs actually decline.
    Before, some profiles had 10 then 10.
    Better: roughly 65-70% then 45-55% of peak LR.
    """
    adjusted = long_runs[:]
    peak_lr = max([lr for lr, phase in zip(adjusted, phases) if phase not in ["Race", "Taper"]] or [8])

    taper_indices = [i for i, phase in enumerate(phases) if phase == "Taper"]

    if len(taper_indices) == 2:
        first = max(6, round((peak_lr * 0.65) / 2) * 2)
        second = max(6, round((peak_lr * 0.50) / 2) * 2)

        # Make sure second taper LR is not equal to or greater than first unless floor forces it.
        if second >= first and first > 6:
            second = first - 2

        adjusted[taper_indices[0]] = first
        adjusted[taper_indices[1]] = second

    elif len(taper_indices) == 1:
        adjusted[taper_indices[0]] = max(6, round((peak_lr * 0.55) / 2) * 2)

    return adjusted


def calc_lrs(weekly, phases, experience, recent_longest_run, runs_per_week):
    lrs = raw_long_runs(weekly, phases, experience, recent_longest_run, runs_per_week)
    lrs = apply_long_run_wave_logic(lrs, phases, experience, runs_per_week)
    lrs = apply_taper_long_runs(lrs, phases, experience, runs_per_week)
    return lrs


# -----------------------------
# WORKOUT GENERATION
# -----------------------------

def primary_workout(weekly_mileage, phase, week_num, experience):
    cap = {
        "beginner": 5,
        "intermediate": 7,
        "advanced": 9,
    }[experience]

    miles = min(cap, max(3, round(weekly_mileage * 0.14)))

    if phase in ["Base", "Build"]:
        styles = [
            "Cruise Intervals",
            "Tempo Blocks",
            "Continuous Tempo",
            "Tempo Progression",
        ]
        return workout("Threshold Session", miles, styles[(week_num - 1) % len(styles)])

    if phase == "Specific":
        styles = [
            "HMP Blocks",
            "Continuous HMP",
            "Progression to HMP",
        ]
        miles = min(cap + 1, max(4, round(weekly_mileage * 0.15)))
        return workout("HMP Session", miles, styles[(week_num - 1) % len(styles)])

    if phase == "Taper":
        # Keep rhythm, but do not turn taper into workout hero week.
        return workout("Threshold Session", min(4, miles), "Continuous Tempo")

    return workout("None", 0)


def secondary_workout(weekly_mileage, phase, week_num, runs_per_week, experience):
    if phase in ["Race", "Taper"]:
        return workout("None", 0)

    if runs_per_week < 5:
        return workout("None", 0)

    # Beginner secondary every week is okay only if 5 days,
    # but keep mileage small.
    cap = {
        "beginner": 4,
        "intermediate": 6,
        "advanced": 7,
    }[experience]

    miles = min(cap, max(3, round(weekly_mileage * 0.10)))

    rotation = [
        ("Hill Strength", "Short Hill Reps"),
        ("Speed Support", "VO2 Support"),
        ("Economy Support", "Strides"),
        ("Speed Support", "10K Support"),
    ]

    category, style = rotation[(week_num - 1) % len(rotation)]
    return workout(category, miles, style)


def long_run_style(phase, week_num, lr, cap):
    if phase == "Race":
        return "Race"

    if phase == "Taper":
        return "Taper LR"

    if phase == "Base":
        return "Steady Finish LR" if week_num % 3 == 0 else "Easy LR"

    if phase == "Build":
        return "Progression LR" if week_num % 2 == 0 else "Easy LR"

    if phase == "Specific":
        if lr >= cap:
            return "Fast Finish LR"
        return "Progression LR"

    return "Easy LR"


# -----------------------------
# WEEKLY SHAPE OPTIMIZER
# -----------------------------

def split_even(total, n):
    if n <= 0:
        return []

    base = total // n
    arr = [base] * n

    leftover = total - base * n
    for i in range(leftover):
        arr[i % len(arr)] += 1

    return arr


def easy_run_soft_cap(runs_per_week, experience):
    """
    Soft caps, not hard rules.
    Advanced runners tolerate more, but low-frequency plans still need control.
    """
    if runs_per_week == 3:
        return 10
    if runs_per_week == 4:
        return 9 if experience != "advanced" else 10
    if runs_per_week == 5:
        return 8 if experience != "advanced" else 10
    if runs_per_week >= 6:
        return 8 if experience == "advanced" else 7

    return 8


def ugly_distribution(z2_runs, lr, runs_per_week, experience, phase):
    if not z2_runs:
        return False

    if phase == "Taper":
        return False

    if phase == "Base":
        if max(z2_runs) > lr and max(z2_runs) >= 9:
            return True
        return False

    soft_cap = easy_run_soft_cap(runs_per_week, experience)

    # LR should remain visually dominant when possible.
    if max(z2_runs) >= lr:
        return True

    # Very close to LR is awkward for 5+ day plans, but only when the easy run
    # is large in absolute terms (12+ mi). A wave-reduced LR of 12 with easy=11
    # is not a real shape problem; LR=14 with easy=13 is.
    if runs_per_week >= 5 and max(z2_runs) >= lr - 1 and max(z2_runs) >= 12:
        return True

    # Multiple oversized easy runs are the main ugly signal.
    oversized = [run for run in z2_runs if run > soft_cap]
    if len(oversized) >= 2:
        return True

    # For 5-day plans, two 11+ mile easy runs feels off. 10-mile days are
    # acceptable for advanced runners at high weekly volume.
    if runs_per_week == 5 and len([run for run in z2_runs if run >= 11]) >= 2:
        return True

    return False


def optimize_week_shape(
    total_mileage,
    lr,
    primary_miles,
    secondary_miles,
    z2_days,
    runs_per_week,
    phase,
    experience,
    lr_ceiling=None,
):
    """
    Repair order:
    1. Try raising LR if phase supports it.
    2. Try adding 1 mile to primary quality.
    3. If still ugly, leave a warning-worthy but mathematically valid week.

    We do NOT force perfection because some high-volume/low-frequency combos are inherently chunky.

    lr_ceiling: when provided, the optimizer will not raise LR above this value.
    Used to prevent the optimizer from undoing deliberate wave-logic reductions.
    """
    cap = lr_cap(experience, runs_per_week)
    effective_ceiling = cap if lr_ceiling is None else lr_ceiling

    if z2_days <= 0:
        return lr, primary_miles, []

    def current_z2(lr_val, primary_val):
        remaining = total_mileage - lr_val - primary_val - secondary_miles
        return split_even(max(0, remaining), z2_days)

    z2_runs = current_z2(lr, primary_miles)

    if not ugly_distribution(z2_runs, lr, runs_per_week, experience, phase):
        return lr, primary_miles, z2_runs

    # Step 1: raise LR, but only in build/specific phases.
    if phase in ["Build", "Specific"]:
        while lr + 2 <= effective_ceiling:
            trial_lr = lr + 2
            trial_z2 = current_z2(trial_lr, primary_miles)

            if not ugly_distribution(trial_z2, trial_lr, runs_per_week, experience, phase):
                return trial_lr, primary_miles, trial_z2

            # Accept improvement even if not perfect.
            if max(trial_z2 or [0]) < max(z2_runs or [0]):
                lr = trial_lr
                z2_runs = trial_z2
            else:
                break

    # Step 2: add 1 mile to primary if that helps and it is not taper.
    if phase not in ["Taper", "Race"]:
        trial_primary = primary_miles + 1
        trial_z2 = current_z2(lr, trial_primary)

        if sum(trial_z2) >= 0 and max(trial_z2 or [0]) <= max(z2_runs or [0]):
            primary_miles = trial_primary
            z2_runs = trial_z2

    return lr, primary_miles, z2_runs



# -----------------------------
# WEEKLY MILEAGE FEASIBILITY
# -----------------------------

def base_week_mileage_adjustment(
    phase,
    mileage,
    lr,
    primary_miles,
    secondary_miles,
    z2_days,
    runs_per_week,
    experience,
):
    """
    In Base, do not force mileage if the result is flat/awkward.

    Example:
    Bad:    31 = Threshold 4 + Secondary 3 + LR 8 + Easy 8 + Easy 8
    Better: 27 = Threshold 4 + Secondary 3 + LR 8 + Easy 6 + Easy 6
    """
    if phase != "Base" or z2_days <= 0:
        return mileage

    soft_cap = easy_run_soft_cap(runs_per_week, experience)
    preferred_easy_cap = min(soft_cap, 7)

    fixed_mileage = lr + primary_miles + secondary_miles
    easy_total = mileage - fixed_mileage

    if easy_total <= 0:
        return mileage

    z2_runs = split_even(easy_total, z2_days)

    flat_lr = max(z2_runs) >= lr
    oversized_easy = max(z2_runs) > preferred_easy_cap

    if flat_lr or oversized_easy:
        adjusted_easy_total = preferred_easy_cap * z2_days
        adjusted_mileage = fixed_mileage + adjusted_easy_total

        # Do not cut more than 4 miles from the original target in one adjustment.
        adjusted_mileage = max(mileage - 4, adjusted_mileage)

        # Never create tiny filler runs.
        adjusted_mileage = max(adjusted_mileage, fixed_mileage + 3 * z2_days)

        return adjusted_mileage

    return mileage


# -----------------------------
# PLAN BUILDER
# -----------------------------

def build_plan(
    experience,
    current_mileage,
    recent_longest_run,
    runs_per_week,
    weeks,
    preferences=None,
):
    validate_engine_inputs(experience, runs_per_week)

    if preferences is None:
        preferences = {
            "long_run_day": "Sat",
            "quality_day": "Tue",
            "unavailable_days": [],
            "preferred_rest_days": ["Sun"],
            "hard_day_style": "spread",
        }

    peak = determine_peak_mileage(
        experience,
        current_mileage,
        weeks,
        runs_per_week,
    )

    recommended_lower, recommended_upper = frequency_peak_range(experience, runs_per_week)
    global_plan_warnings = []
    if current_mileage > recommended_upper:
        global_plan_warnings.append(
            f"Current mileage ({current_mileage} mi/week) exceeds the recommended cap "
            f"for {experience} / {runs_per_week} days ({recommended_upper} mi/week). "
            "Plan is allowed because you already report handling this volume, but weeks may be dense. "
            "Consider adding a run day or choosing a lower-volume plan."
        )

    phases = build_phases(weeks)
    weekly = weekly_curve(peak, phases, current_mileage)

    # Compute pre-wave LRs so the shape optimizer knows which weeks were
    # intentionally reduced by wave logic and should not be raised back up.
    pre_wave_lrs = raw_long_runs(weekly, phases, experience, recent_longest_run, runs_per_week)
    long_runs = calc_lrs(
        weekly,
        phases,
        experience,
        recent_longest_run,
        runs_per_week,
    )

    plan = []
    cap = lr_cap(experience, runs_per_week)

    for i in range(weeks):
        week_num = i + 1
        phase = phases[i]
        mileage = weekly[i]

        if phase == "Race":
            sessions = {
                "primary": None,
                "secondary": None,
                "lr": 0,
                "lr_style": "Race",
                "z2_runs": [3, 3],
            }
            schedule_data = build_week_schedule(sessions, phase, preferences)
            plan.append({
                "week": week_num,
                "phase": phase,
                "mileage": 6,
                "sessions": sessions,
                "primary": None,
                "secondary": None,
                "lr": 0,
                "lr_style": "Race",
                "z2_runs": [3, 3],
                "schedule": schedule_data["schedule"],
                "warnings": schedule_data["warnings"],
                "plan_warnings": global_plan_warnings,
                "peak_mileage": peak,
            })
            continue

        primary = primary_workout(mileage, phase, week_num, experience)
        secondary = secondary_workout(mileage, phase, week_num, runs_per_week, experience)

        quality_days = 1
        if primary["miles"] > 0:
            quality_days += 1
        if secondary["miles"] > 0:
            quality_days += 1

        z2_days = max(0, runs_per_week - quality_days)

        lr = long_runs[i]

        # V5.3: In Base, trim weekly mileage slightly if the target creates
        # flat/awkward structure like LR 8 with Easy 8 / 8.
        mileage = base_week_mileage_adjustment(
            phase,
            mileage,
            lr,
            primary["miles"],
            secondary["miles"],
            z2_days,
            runs_per_week,
            experience,
        )

        # If wave logic reduced this LR, lock the ceiling so the optimizer
        # cannot raise it back to cap and undo the wave reduction.
        lr_ceiling = long_runs[i] if long_runs[i] < pre_wave_lrs[i] else cap

        lr, primary_miles, z2_runs = optimize_week_shape(
            mileage,
            lr,
            primary["miles"],
            secondary["miles"],
            z2_days,
            runs_per_week,
            phase,
            experience,
            lr_ceiling=lr_ceiling,
        )

        primary["miles"] = primary_miles

        # Cap combined quality (primary + secondary) after the shape optimizer
        # has run.  Trimming at this stage prevents the optimizer from raising
        # primary to compensate and undoing the cap.  Any miles removed from
        # secondary are returned to z2_runs so the weekly total stays correct.
        # Advanced plans use a tighter 25 % budget; others 28 % so that only
        # genuinely overloaded high-mileage advanced peak weeks are affected.
        quality_budget_pct = 0.25 if experience == "advanced" else 0.28
        quality_budget = round(mileage * quality_budget_pct)
        combined_quality = primary["miles"] + secondary["miles"]
        if combined_quality > quality_budget and secondary["miles"] > 0:
            excess = combined_quality - quality_budget
            secondary["miles"] = max(0, secondary["miles"] - excess)
            if z2_runs:
                z2_runs = split_even(sum(z2_runs) + excess, len(z2_runs))

        warnings = []

        planned_total = primary["miles"] + secondary["miles"] + lr + sum(z2_runs)
        if planned_total != mileage:
            warnings.append(f"Math check: planned mileage is {planned_total}, target is {mileage}.")

        if ugly_distribution(z2_runs, lr, runs_per_week, experience, phase):
            warnings.append("Weekly shape is chunky. Consider more run days or lower peak mileage.")

        sessions = {
            "primary": primary,
            "secondary": secondary,
            "lr": lr,
            "lr_style": long_run_style(phase, week_num, lr, cap),
            "z2_runs": z2_runs,
        }

        schedule_data = build_week_schedule(sessions, phase, preferences)
        warnings.extend(schedule_data["warnings"])

        plan.append({
            "week": week_num,
            "phase": phase,
            "mileage": mileage,
            "sessions": sessions,
            "primary": primary,
            "secondary": secondary,
            "lr": lr,
            "lr_style": sessions["lr_style"],
            "z2_runs": z2_runs,
            "schedule": schedule_data["schedule"],
            "warnings": warnings,
            "plan_warnings": global_plan_warnings,
            "peak_mileage": peak,
        })

    return peak, plan


# -----------------------------
# PRINT PLAN
# -----------------------------

def print_plan(peak, plan, show_styles=True, show_schedule=True, show_glossary=False):
    print("\nHALF MARATHON PLAN MAIN 4PLUS V5.7\n")
    print(f"Peak Mileage: {peak} mi\n")

    if plan and plan[0].get("plan_warnings"):
        print("Plan Notes:")
        for warning in plan[0]["plan_warnings"]:
            print(f"  - {warning}")
        print()

    for week in plan:
        print(f"Week {week['week']} | {week['phase']} | {week['mileage']} mi")

        if week["phase"] == "Race":
            print("  Race Week")
            print("  Easy Runs:", week["z2_runs"])
        else:
            primary = week["primary"]
            secondary = week["secondary"]

            if primary and primary["miles"] > 0:
                print(f"  Primary: {primary['category']} ({primary['miles']})")
                if show_styles and primary["suggested_style"]:
                    print(f"    Suggested Style: {primary['suggested_style']}")

            if secondary and secondary["miles"] > 0:
                print(f"  Secondary: {secondary['category']} ({secondary['miles']})")
                if show_styles and secondary["suggested_style"]:
                    print(f"    Suggested Style: {secondary['suggested_style']}")

            print(f"  Long Run: {week['lr_style']} ({week['lr']})")
            print("  Easy Runs:", week["z2_runs"])

        if show_schedule and "schedule" in week:
            print("  Schedule:")
            for day, item in week["schedule"].items():
                print(f"    {day}: {schedule_label(item, show_styles=False)}")

        if week["warnings"]:
            print("  Notes:")
            for warning in week["warnings"]:
                print(f"    - {warning}")

        print()

    if show_glossary:
        print_workout_glossary()


# -----------------------------
# MAIN TEST
# -----------------------------

if __name__ == "__main__":
    peak, plan = build_plan(
        experience="intermediate",
        current_mileage=25,
        recent_longest_run=8,
        runs_per_week=5,
        weeks=12,
    )

    print_plan(peak, plan)
