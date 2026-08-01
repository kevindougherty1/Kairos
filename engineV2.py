import math
import random


MIN_PEAK = 35
MAX_PEAK = 70


# -----------------------------
# PEAK MILEAGE ENGINE
# -----------------------------

def determine_peak_mileage(experience,current_mileage,weeks):

    ranges = {
        "beginner":(35,45),
        "intermediate":(45,55),
        "advanced":(55,70)
    }

    lower,upper = ranges[experience]

    growth_weeks = weeks-3

    ramp_peak = current_mileage*(1.07**growth_weeks)

    ramp_peak = round(ramp_peak)

    peak = min(upper,ramp_peak)

    peak = max(lower,peak)

    peak = min(MAX_PEAK,max(MIN_PEAK,peak))

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

    def build_segment(start, end, n, cutback=False):
        if n == 0:
            return []

        segment = []

        for i in range(1, n + 1):
            progress = (i / n)

            # slow early ramp, faster later
            progress = progress ** 1.25

            val = round(start + (end - start) * progress)
            segment.append(val)

        if cutback and n >= 4:
            segment[-1] = round(segment[-2] * 0.85)

        return segment

    # Base
    base_segment = build_segment(
        start=current_mileage,
        end=base_target,
        n=base_n,
        cutback=True
    )
    weekly += base_segment

    # Build starts from wherever Base ended
    build_start = weekly[-1] if weekly else current_mileage
    build_segment_vals = build_segment(
        start=build_start,
        end=build_target,
        n=build_n,
        cutback=True
    )
    weekly += build_segment_vals

    # Peak starts from wherever Build ended
    peak_start = weekly[-1] if weekly else current_mileage
    peak_segment_vals = build_segment(
        start=peak_start,
        end=peak_target,
        n=peak_n,
        cutback=False
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
        weekly += [8]

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

def calculate_long_runs(weekly, phases, peak, recent_long_run):

    long_runs = []
    prev_lr = 0
    twenty_count = 0
    last_was_twenty = False

    phase_pct = {
        "Base": 0.32,
        "Build": 0.34,
        "Peak": 0.36
    }

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

        # First week anchor
        if prev_lr == 0:
            lr = max(recent_long_run, target_lr)
        else:
            lr = min(target_lr, prev_lr + 2)

        # Ensure LR not too small
        min_lr = round(mileage * 0.30)
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
        if phase == "Peak" and mileage == peak_week_mileage:
            lr = min(20, round(mileage * 0.36))

        # Cap at 20
        lr = min(lr, 20)

        # Control 20 milers
        if lr == 20:
            if last_was_twenty:
                lr = 18
                last_was_twenty = False
            elif twenty_count >= 2:
                lr = 18
                last_was_twenty = False
            else:
                twenty_count += 1
                last_was_twenty = True
        else:
            last_was_twenty = False

        # Even rounding
        lr = round(lr / 2) * 2
        lr = max(8, lr)

        long_runs.append(lr)
        prev_lr = lr

    return long_runs

# -----------------------------
# SESSION DISTRIBUTION
# -----------------------------

def distribute_runs(mileage, lr, vo2, tempo, runs_per_week, phase, week_num, base_weeks):

    if lr == 0:
        return {
            "z2_runs": [3, 3, 2],
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
            runs_per_week >= 5
            and lr > 0
            and phase in ["Build", "Peak"]
    )

    # -----------------------------
    # MEDIUM LONG RUN
    # -----------------------------
    mlr = 0

    if mlr_allowed:

        trial_mlr = round(lr * random.uniform(0.66, 0.73))

        lower = round(lr * 0.65)
        upper = round(lr * 0.75)

        trial_mlr = max(lower, min(trial_mlr, upper))
        trial_mlr = min(trial_mlr, lr - 2)

        # only keep MLR if remaining Z2 runs can still be real runs
        trial_z2_days = runs_per_week - quality_days - 1
        remaining_after_mlr = mileage - lr - vo2 - tempo - trial_mlr

        if trial_z2_days > 0 and remaining_after_mlr >= 2.5 * trial_z2_days:
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
    # ensure LR biggest run
    # -----------------------------
    if z2_runs:

        max_z2 = max(z2_runs)

        if max_z2 >= lr:

            diff = max_z2 - (lr - 1)
            idx = z2_runs.index(max_z2)

            z2_runs[idx] -= diff
            lr += diff

    # easy run floor
    z2_runs = [max(3, r) for r in z2_runs]

    if phase == "Taper":
        z2_runs = [min(r, 6) for r in z2_runs]

    return {
        "z2_runs": z2_runs,
        "tempo": tempo,
        "vo2": vo2,
        "lr": lr,
        "mlr": mlr
    }

# -----------------------------
# BUILD PLAN
# -----------------------------

def build_plan(
        experience,
        current_mileage,
        longest_run,
        runs_per_week,
        weeks):


    peak = determine_peak_mileage(
        experience,
        current_mileage,
        weeks
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
        longest_run
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

        plan.append({
            "week": i + 1,
            "phase": phases[i],
            "mileage": weekly[i],
            "sessions": sessions
        })

    return plan

# -----------------------------
# PRINT PLAN
# -----------------------------

def print_plan(plan):

    print("\nMARATHON PLAN V2\n")

    for week in plan:

        s=week["sessions"]

        print(f"Week {week['week']} | {week['phase']} | Mileage {week['mileage']}")

        if week["phase"]=="Race":

            print("  Z2 Runs:",s["z2_runs"])

        else:

            print("  VO2:",s["vo2"])

            if s["tempo"]>0:

                print("  Tempo:",s["tempo"])

            print("  Long Run:", s["lr"])

            if s["mlr"] > 0:
                print("  Medium Long:", s["mlr"])

            print("  Z2 Runs:", s["z2_runs"])

        print()


# -----------------------------
# MAIN
# -----------------------------

if __name__=="__main__":

    plan=build_plan(
        experience="intermediate",
        current_mileage=25,
        longest_run=10,
        runs_per_week=6,
        weeks=16
    )

    print_plan(plan)