import math
import random


MIN_PEAK = 35
MAX_PEAK = 70

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def day_index(day):
    return DAYS.index(day)


def offset_day(day, offset):
    idx = (day_index(day) + offset) % 7
    return DAYS[idx]

def tempo_candidates(long_run_day):
    # prefer day before LR, then 2 days before LR
    return [
        offset_day(long_run_day, -1),
        offset_day(long_run_day, -2)
    ]


def mlr_candidates(long_run_day):
    # best spacing first
    return [
        offset_day(long_run_day, -3),
        offset_day(long_run_day, -4),
        offset_day(long_run_day, -2),
        offset_day(long_run_day, -5),
        offset_day(long_run_day, -6),
        offset_day(long_run_day, -1)
    ]

def is_available(day, schedule, unavailable_days):
    return schedule[day] == "Rest" and day not in unavailable_days

def choose_best_day(candidates, schedule, unavailable_days, preferred_rest_days):
    # First try days that are open, available, and NOT preferred rest days
    for day in candidates:
        if (
            schedule[day] == "Rest"
            and day not in unavailable_days
            and day not in preferred_rest_days
        ):
            return day

    # If none exist, allow preferred rest days as fallback
    for day in candidates:
        if (
            schedule[day] == "Rest"
            and day not in unavailable_days
        ):
            return day

    return None

# -----------------------------
# PEAK MILEAGE ENGINE
# -----------------------------

# Peak ceiling per (experience, runs_per_week). A 5-day runner can't sustainably
# hit a 70 mpw peak — the math forces oversized "easy" days (a 70 mpw runner
# on 5 days averages 14 mi/run). To push past your frequency's cap, add a day.
# 7-day plans are rejected upstream in build_plan().
PEAK_TABLE = {
    "beginner":     {4: 32, 5: 38, 6: 45},
    "intermediate": {4: 42, 5: 50, 6: 55},
    "advanced":     {4: 52, 5: 60, 6: 70},
}


def frequency_peak_range(experience, runs_per_week):
    upper = PEAK_TABLE[experience][runs_per_week]
    lower = round(upper * 0.70)
    return lower, upper


def determine_peak_mileage(experience, current_mileage, weeks, runs_per_week):
    lower, upper = frequency_peak_range(experience, runs_per_week)

    growth_weeks = weeks - 3
    ramp_peak = round(current_mileage * (1.07 ** growth_weeks))

    peak = min(upper, ramp_peak)
    peak = max(lower, peak)

    # Honor current_mileage as a floor only up to the frequency cap. An
    # over-qualified runner (e.g., 60 mpw on 5d) gets peak clamped at their
    # frequency's upper bound rather than being given an unsustainable plan.
    peak = max(peak, min(current_mileage, upper))

    return peak


# -----------------------------
# PHASE GENERATION
# -----------------------------

def build_phases(weeks):

    race_weeks = 1
    taper_weeks = 2
    dev_weeks = weeks-race_weeks-taper_weeks

    base = round(dev_weeks*0.35)
    build = round(dev_weeks*0.40)
    peak = dev_weeks-base-build

    phases = (
        ["Base"]*base+
        ["Build"]*build+
        ["Peak"]*peak+
        ["Taper"]*taper_weeks+
        ["Race"]*race_weeks
    )

    return phases


# -----------------------------
# MILEAGE CURVE
# -----------------------------

def linspace(start,end,n):

    if n==1:
        return [start]

    step=(end-start)/(n-1)

    return [start+i*step for i in range(n)]


def build_curve(phases):

    curve=[]

    base_n=phases.count("Base")
    build_n=phases.count("Build")
    peak_n=phases.count("Peak")

    curve+=linspace(0.58,0.72,base_n)
    curve+=linspace(0.74,0.90,build_n)
    curve+=linspace(0.92,1.00,peak_n)

    curve+=[0.78,0.58]
    curve+=[0.18]

    return curve


def generate_weekly_mileage(
    peak,
    phases,
    current_mileage,
    experience
):
    weekly = []

    base_n = phases.count("Base")
    build_n = phases.count("Build")
    peak_n = phases.count("Peak")
    taper_n = phases.count("Taper")
    race_n = phases.count("Race")

    base_target = round(peak * 0.82)
    build_target = round(peak * 0.95)
    peak_target = peak

    def build_segment(start, end, n, cutback=False, cutback_floor=None, exponent=1.25):
        if n == 0:
            return []

        segment = []

        for i in range(1, n + 1):
            progress = (i / n) ** exponent
            val = round(start + (end - start) * progress)
            segment.append(val)

        if cutback and n >= 4:
            cutback_val = round(segment[-2] * 0.85)
            if cutback_floor is not None:
                cutback_val = max(cutback_val, cutback_floor)
            segment[-1] = cutback_val

        return segment

    # Compute the minimum Build-cutback floor. The Peak phase must climb from
    # the cutback to peak with no week-over-week jump exceeding max(+10%, +4 mi).
    # Step backward from peak `peak_n` times to find the lowest acceptable
    # cutback week. Mirrors the HM engine's fix.
    MAX_PCT = 0.10
    MAX_ABS = 4
    min_cutback = peak_target
    for _ in range(peak_n):
        floor_by_pct = math.ceil(min_cutback / (1 + MAX_PCT))
        floor_by_abs = min_cutback - MAX_ABS
        min_cutback = min(floor_by_pct, floor_by_abs)

    # Base is the establishment phase — gentle ramp, no cutback. Cutbacks are
    # a recovery mechanism after a meaningful training load, which doesn't
    # apply until Build. Previously Base had `cutback=True` which produced a
    # trough between Base and Build (e.g., int 25/5d: 28→31→36→40→34→36, the
    # 40→34 drop served no training purpose).
    base_segment = build_segment(
        start=current_mileage,
        end=base_target,
        n=base_n,
        cutback=False,
    )
    weekly += base_segment

    # Build starts from wherever Base ended
    build_start = weekly[-1] if weekly else current_mileage
    build_segment_vals = build_segment(
        start=build_start,
        end=build_target,
        n=build_n,
        cutback=True,
        cutback_floor=min_cutback,
    )
    weekly += build_segment_vals

    # Peak starts from wherever Build ended. Linear interpolation (exponent=1.0)
    # so the curve's own easing doesn't put the steepest jump on the climb to
    # peak — that's exactly where we don't want a spike.
    peak_start = weekly[-1] if weekly else current_mileage
    peak_segment_vals = build_segment(
        start=peak_start,
        end=peak_target,
        n=peak_n,
        cutback=False,
        exponent=1.0,
    )
    weekly += peak_segment_vals

    # Taper
    if taper_n == 2:
        weekly += [round(peak * 0.75), round(peak * 0.55)]
    elif taper_n == 1:
        weekly += [round(peak * 0.60)]
    elif taper_n == 3:
        weekly += [round(peak * 0.80), round(peak * 0.65), round(peak * 0.50)]

    # Race
    if race_n == 1:
        weekly += [6]

    # Global week-over-week guardrail. No climbing week jumps more than
    # max(+10%, +4 mi) over the prior week. This is the engine's overall
    # "don't spit out" rule — it keeps the curve honest regardless of how
    # phase math, current_mileage, or peak interact upstream. Cutbacks
    # (drops) and Taper/Race weeks are left alone.
    MAX_PCT = 0.10
    MAX_ABS = 4
    for i in range(1, len(weekly)):
        if phases[i] in ("Taper", "Race"):
            continue
        prev = weekly[i - 1]
        max_jump = max(round(prev * MAX_PCT), MAX_ABS)
        if weekly[i] - prev > max_jump:
            weekly[i] = prev + max_jump

    return weekly


# -----------------------------
# TEMPO SCHEDULE
# -----------------------------

def tempo_schedule(phases):

    tempo=[]
    toggle=True

    for phase in phases:

        if phase in ["Base","Build"]:

            tempo.append(toggle)
            toggle=not toggle

        else:
            tempo.append(False)

    return tempo


# -----------------------------
# VO2 MILEAGE
# -----------------------------

def vo2_mileage(peak, phase):

    base = round(peak * 0.10)

    if phase == "Race":
        return 0

    if phase == "Base":
        return round(base * 0.8)

    if phase == "Build":
        return base

    if phase == "Peak":
        return round(base * 1.1)

    if phase == "Taper":
        return round(base * 0.6)

    return base


# -----------------------------
# TEMPO MILEAGE
# -----------------------------

def tempo_mileage(weekly,enabled):

    if not enabled:
        return 0

    return min(6,round(weekly*0.15))


# -----------------------------
# LONG RUN ENGINE
# -----------------------------

def calculate_long_runs(weekly, phases, peak, recent_long_run, experience="intermediate"):

    long_runs = []
    prev_lr = 0
    last_was_twenty = False

    # Advanced runners have high enough weekly volume that 32% of weekly in
    # Base produces 18-mile Base LRs — too aggressive for an establishment
    # phase. Drop their Base % so the absolute LR stays in the 14-16 range
    # for Base, then climbs in Build/Peak.
    if experience == "advanced":
        phase_pct = {"Base": 0.28, "Build": 0.32, "Peak": 0.36}
    else:
        phase_pct = {"Base": 0.32, "Build": 0.34, "Peak": 0.36}

    peak_week_mileage = max(weekly)

    for i, (mileage, phase) in enumerate(zip(weekly, phases)):

        # Race week
        if phase == "Race":
            long_runs.append(0)
            last_was_twenty = False
            continue

        # Taper
        if phase == "Taper":

            peak_lr = max(long_runs)

            if i == len(phases) - 3:
                lr = round(peak_lr * 0.70)
            else:
                lr = round(peak_lr * 0.50)

            lr = round(lr / 2) * 2

            long_runs.append(lr)
            prev_lr = lr
            last_was_twenty = False
            continue

        pct = phase_pct.get(phase, 0.34)
        target_lr = round(mileage * pct)

        # First week: phase logic drives the value. recent_long_run is a soft
        # regression floor (don't drop below ~70% of recent capability), not a
        # value that lifts the LR upward. A runner who recently ran 18 mi gets
        # a sensible Base-phase LR target, not 18 again — the plan is allowed
        # to establish a softer baseline.
        if prev_lr == 0:
            regression_floor = round(recent_long_run * 0.70)
            lr = max(target_lr, regression_floor)
        else:
            lr = min(target_lr, prev_lr + 2)

        # Ensure LR not too small. Floor must sit below the phase target so it
        # doesn't fight the phase_pct (advanced Base targets 0.28; a 0.30 floor
        # would force advanced Base LRs back up to 18-20).
        min_lr_pct = 0.27 if experience == "advanced" else 0.30
        min_lr = round(mileage * min_lr_pct)
        lr = max(lr, min_lr)

        # Prevent stagnation in Base
        if phase == "Base" and prev_lr > 0 and lr == prev_lr:
            lr += 2

        # Prevent weird drops in Build/Peak
        if prev_lr > 0 and lr < prev_lr and phase in ["Build", "Peak"]:
            lr = prev_lr

        # Step-down only when mileage drops
        if len(long_runs) >= 2 and phase in ["Build", "Peak"]:
            if mileage < weekly[i - 1]:
                lr = max(prev_lr - 2, round(mileage * 0.30))

        if phase == "Peak" and prev_lr < 18:
            lr = max(lr, prev_lr + 2)

        # Protect Peak phase from unnecessary drops
        if phase == "Peak" and prev_lr >= 18 and lr < prev_lr:
            lr = prev_lr

        # Force peak LR during highest mileage week
        is_peak_week = (phase == "Peak" and mileage == peak_week_mileage)
        if is_peak_week:
            lr = min(20, round(mileage * 0.36))

        # Even rounding happens BEFORE the 20-control so the control sees the
        # final LR value. Previously round(19/2)*2 = 20 (banker's rounding)
        # produced stealth 20-milers that bypassed the spacing rule.
        lr = round(lr / 2) * 2
        lr = max(8, lr)

        # Re-check Base stagnation after rounding — `lr=17` next to `prev=16`
        # looks non-stagnant pre-rounding but rounds to 16 (stagnant).
        if phase == "Base" and prev_lr > 0 and lr == prev_lr:
            lr += 2

        # Advanced Base LR ceiling. Recreational-advanced (Kairos's audience)
        # plans like Pfitzinger, Higdon, and Hanson cap Base-phase LRs at 16.
        # 18-mile Base LRs are pro/elite territory — unsupervised, that's risky.
        # Build/Peak still climb to 18-20.
        if phase == "Base" and experience == "advanced":
            lr = min(lr, 16)

        # If after the cap we'd be flat at 16 (because the +2 stagnation bump
        # just got clipped), vary downward so the Base LR pattern alternates
        # (16, 14, 16, 14, 16) instead of stagnating. Only fires for advanced
        # Base at the cap.
        if (
            phase == "Base"
            and experience == "advanced"
            and prev_lr > 0
            and lr == prev_lr == 16
        ):
            lr = 14

        # Universal LR-to-weekly ceiling: 40% of the week's mileage. Coaching
        # standard is 30-35%; 40% is the upper bound past which the long run
        # overweights the week's stress and injury risk climbs. This bites
        # mostly at low volume (e.g., 4-day beginner Base where target_lr +
        # stagnation bump can push LR to 48% of weekly).
        lr = min(lr, int(mileage * 0.40))

        # Cap at 20
        lr = min(lr, 20)

        # Spacing rule: no back-to-back 20-mile LRs. Peak week is sacred —
        # the highest-mileage week always gets its 20 regardless of spacing.
        # No total cap on 20-milers: an advanced runner's Peak phase legitimately
        # has 2-3 of them across the plan, and capping at 2 total cuts off Peak.
        if lr == 20:
            if last_was_twenty and not is_peak_week:
                lr = 18
                last_was_twenty = False
            else:
                last_was_twenty = True
        else:
            last_was_twenty = False

        long_runs.append(lr)
        prev_lr = lr

    return long_runs

# -----------------------------
# SESSION DISTRIBUTION
# -----------------------------

def distribute_runs(mileage, lr, vo2, tempo, runs_per_week, phase, week_num, base_weeks):

    if lr == 0:
        return {
            "z2_runs": [3, 3],
            "tempo": 0,
            "vo2": 0,
            "lr": 0,
            "mlr": 0
        }

    quality_days = 1

    if vo2 > 0:
        quality_days += 1

    if tempo > 0:
        quality_days += 1

    # -----------------------------
    # MLR eligibility
    # -----------------------------
    late_base_start = math.ceil(base_weeks / 2)

    mlr_allowed = (
            runs_per_week >= 6
            and lr > 0
            and phase in ["Build", "Peak"]
    )

    # -----------------------------
    # MEDIUM LONG RUN
    # -----------------------------
    mlr = 0

    if mlr_allowed:

        # deterministic base
        trial_mlr = round(lr * 0.70)

        # clamp to acceptable range
        lower = round(lr * 0.65)
        upper = round(lr * 0.75)

        trial_mlr = max(lower, min(trial_mlr, upper))

        # ensure it's meaningfully smaller than LR
        trial_mlr = min(trial_mlr, lr - 2)

        # -----------------------------
        # viability check
        # -----------------------------
        trial_z2_days = runs_per_week - quality_days - 1
        remaining_after_mlr = mileage - lr - vo2 - tempo - trial_mlr

        if trial_z2_days > 0 and remaining_after_mlr >= 2 * trial_z2_days:
            mlr = trial_mlr

    # -----------------------------
    # Remaining mileage
    # -----------------------------
    remaining = max(0, mileage - lr - vo2 - tempo - mlr)

    # -----------------------------
    # Z2 days
    # -----------------------------
    z2_days = runs_per_week - quality_days - (1 if mlr > 0 else 0)

    z2_runs = []

    if z2_days > 0:

        per_day = remaining // z2_days

        for _ in range(z2_days):
            z2_runs.append(per_day)

        leftover = remaining - per_day * z2_days

        for i in range(leftover):
            z2_runs[i] += 1

    # -----------------------------
    # ensure LR biggest run — SKIP in Taper. Taper LRs are intentionally
    # smaller than Peak; lifting them to dominate easy runs produces the
    # nonsensical "Taper LR > Peak LR" pattern. In low-frequency Taper weeks
    # one easy day will be long, but that's the math of the mileage target.
    #
    # The lift is also bounded by the 40% LR-to-weekly ceiling. At low volume
    # with multiple quality days, the leftover easy day can be larger than
    # the LR — lifting LR all the way to dominate it would push the LR past
    # 40% of weekly. In that case the LR settles at the cap and an easy day
    # may be tied with (or slightly larger than) the LR.
    # -----------------------------
    if z2_runs and phase != "Taper":

        max_z2 = max(z2_runs)

        if max_z2 >= lr:

            ideal_lr = max_z2 + 1
            capped_lr = min(ideal_lr, int(mileage * 0.40))
            diff = capped_lr - lr

            if diff > 0:
                idx = z2_runs.index(max_z2)
                z2_runs[idx] -= diff
                lr += diff

    # easy run floor
    z2_runs = [max(3, r) for r in z2_runs]

    # Note: previously Taper z2 runs were capped at 6 mi for recovery purposes,
    # but that cap created systemic mileage leaks (e.g., adv 6d Taper Wk 16
    # would report 52 mi while the schedule summed to 36). The Taper mileage
    # target itself encodes the recovery — capping individual runs on top of
    # that just makes the plan internally inconsistent.

    return {
        "z2_runs": z2_runs,
        "tempo": tempo,
        "vo2": vo2,
        "lr": lr,
        "mlr": mlr
    }

def build_week_schedule_v2(sessions, phase, preferences, runs_per_week):
    schedule = {day: "Rest" for day in DAYS}
    warnings = []

    lr = sessions["lr"]
    mlr = sessions["mlr"]
    vo2 = sessions["vo2"]
    tempo = sessions["tempo"]
    z2_runs = sessions["z2_runs"][:]

    long_run_day = preferences["long_run_day"]
    speed_day = preferences["speed_day"]
    unavailable_days = preferences.get("unavailable_days", [])
    preferred_rest_days = preferences.get("preferred_rest_days", [])

    # -----------------------------
    # Race week
    # -----------------------------
    if phase == "Race":
        schedule[long_run_day] = "Race"

        shakeout_days = []
        for d in [offset_day(long_run_day, -5), offset_day(long_run_day, -3)]:
            if d not in unavailable_days and schedule[d] == "Rest":
                shakeout_days.append(d)

        if len(shakeout_days) > 0:
            schedule[shakeout_days[0]] = "Shakeout (3)"
        if len(shakeout_days) > 1:
            schedule[shakeout_days[1]] = "Shakeout (3)"

        return {"schedule": schedule, "warnings": warnings}

    # -----------------------------
    # Place Long Run
    # -----------------------------
    if long_run_day in unavailable_days:
        warnings.append(f"Long run day {long_run_day} is unavailable.")
    else:
        schedule[long_run_day] = f"Long Run ({lr})"

    # -----------------------------
    # Place Speed Day
    # -----------------------------
    if vo2 > 0:
        if speed_day == long_run_day:
            warnings.append("Speed day conflicts with long run day.")
        elif speed_day in unavailable_days:
            warnings.append(f"Speed day {speed_day} is unavailable.")
        elif schedule[speed_day] != "Rest":
            warnings.append(f"Speed day {speed_day} is already occupied.")
        else:
            schedule[speed_day] = f"VO2 ({vo2})"

    # -----------------------------
    # Place Tempo before LR
    # -----------------------------
    if tempo > 0:
        candidates = [d for d in tempo_candidates(long_run_day) if d != speed_day]

        chosen_day = choose_best_day(
            candidates,
            schedule,
            unavailable_days,
            preferred_rest_days
        )

        if chosen_day:
            schedule[chosen_day] = f"Tempo ({tempo})"
        else:
            warnings.append("Could not place tempo in preferred slot before long run.")


    # -----------------------------
    # Place MLR with optimal spacing from LR
    # -----------------------------
    if mlr > 0:
        candidates = [d for d in mlr_candidates(long_run_day) if d != speed_day]

        chosen_day = choose_best_day(
            candidates,
            schedule,
            unavailable_days,
            preferred_rest_days
        )

        if chosen_day:
            schedule[chosen_day] = f"MLR ({mlr})"
        else:
            warnings.append("Could not place MLR in an ideal slot.")

    # -----------------------------
    # Fill Z2 Runs
    # -----------------------------
    remaining_days = [
        day for day in DAYS
        if is_available(day, schedule, unavailable_days)
           and day not in preferred_rest_days
    ]

    for day in remaining_days:
        if z2_runs:
            schedule[day] = f"Z2 ({z2_runs.pop(0)})"

    # fallback: use preferred rest days only if needed
    for day in preferred_rest_days:
        if z2_runs and is_available(day, schedule, unavailable_days):
            schedule[day] = f"Z2 ({z2_runs.pop(0)})"
            warnings.append(f"Preferred rest day {day} was used for a run.")

    if z2_runs:
        warnings.append("Not all Z2 runs could be placed.")

    return {
        "schedule": schedule,
        "warnings": warnings
    }



# -----------------------------
# BUILD PLAN
# -----------------------------

def build_plan(
        experience,
        current_mileage,
        longest_run,
        runs_per_week,
        weeks,
        preferences):

    if runs_per_week > 6:
        raise ValueError(
            "7-day plans are not supported. Running 7 days a week for 16+ weeks "
            "without a rest day is not healthy for the runners Kairos targets. "
            "Choose 4-6 days per week."
        )
    if runs_per_week < 4:
        raise ValueError(
            "Marathon engine supports 4-6 run days per week. "
            "Use a separate low-frequency engine for 3-day plans."
        )

    peak = determine_peak_mileage(
        experience,
        current_mileage,
        weeks,
        runs_per_week,
    )

    phases = build_phases(weeks)

    weekly = generate_weekly_mileage(
        peak,
        phases,
        current_mileage,
        experience
    )

    tempo_flags = tempo_schedule(phases)

    long_runs = calculate_long_runs(
        weekly,
        phases,
        peak,
        longest_run,
        experience,
    )

    plan = []

    base_weeks = phases.count("Base")


    for i in range(weeks):

        vo2 = vo2_mileage(peak, phases[i])

        tempo = tempo_mileage(
            weekly[i],
            tempo_flags[i]
        )

        rpw = runs_per_week - 1 if phases[i] == "Taper" else runs_per_week

        sessions = distribute_runs(
            weekly[i],
            long_runs[i],
            vo2,
            tempo,
            rpw,
            phases[i],
            i + 1,
            base_weeks
        )

        # OLD:
        # schedule = build_week_schedule(
        #     sessions,
        #     phases[i],
        #     rpw
        # )

        # NEW:
        schedule_data = build_week_schedule_v2(
            sessions,
            phases[i],
            preferences,
            rpw
        )

        plan.append({
            "week": i + 1,
            "phase": phases[i],
            "mileage": weekly[i],
            "sessions": sessions,
            "schedule": schedule_data["schedule"],
            "warnings": schedule_data["warnings"]
        })

    return plan

# -----------------------------
# PRINT PLAN
# -----------------------------

def print_plan(plan):

    print("\nMARATHON PLAN V2\n")

    for week in plan:

        s = week["sessions"]
        sched = week["schedule"]
        warnings = week.get("warnings", [])

        print(f"Week {week['week']} | {week['phase']} | Mileage {week['mileage']}")

        if week["phase"] == "Race":
            print("  Z2 Runs:", s["z2_runs"])
        else:
            print("  VO2:", s["vo2"])

            if s["tempo"] > 0:
                print("  Tempo:", s["tempo"])

            print("  Long Run:", s["lr"])

            if s["mlr"] > 0:
                print("  Medium Long:", s["mlr"])

            print("  Z2 Runs:", s["z2_runs"])

        print("  Schedule:")
        for day, workout in sched.items():
            print(f"    {day}: {workout}")

        if warnings:
            print("  Warnings:")
            for w in warnings:
                print(f"    - {w}")

        print()

# -----------------------------
# MAIN
# -----------------------------

if __name__=="__main__":

    preferences = {
        "long_run_day": "Sat",
        "speed_day": "Tue",
        "unavailable_days": [],
        "preferred_rest_days": ["Sun"],
    }

    plan = build_plan(
        experience="intermediate",
        current_mileage=25,
        longest_run=10,
        runs_per_week=6,
        weeks=16,
        preferences=preferences
    )

    print_plan(plan)