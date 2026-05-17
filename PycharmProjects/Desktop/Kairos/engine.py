import math

WEEKS = 14

MILEAGE_CURVE = [
    0.58,0.62,0.68,0.63,
    0.72,0.78,0.84,0.80,
    0.90,1.00,0.96,
    0.75,0.55,0.18
]

PHASES = [
    "Base","Base","Base","Base",
    "Build","Build","Build","Build",
    "Peak","Peak","Peak",
    "Taper","Taper","Race"
]


# -----------------------------
# WEEKLY MILEAGE
# -----------------------------

def generate_weekly_mileage(peak):

    weekly = []

    for i,pct in enumerate(MILEAGE_CURVE):

        if PHASES[i] == "Race":
            weekly.append(8)
        else:
            weekly.append(round(peak * pct))

    return weekly


# -----------------------------
# LONG RUN
# -----------------------------

def calculate_long_runs(weekly, peak):

    long_runs = []
    prev_lr = 0
    twenty_count = 0

    for i,mileage in enumerate(weekly):

        phase = PHASES[i]

        if phase == "Race":
            long_runs.append(0)
            continue

        if phase == "Base":
            pct = 0.30
        elif phase == "Build":
            pct = 0.35
        elif phase == "Peak":
            pct = 0.40
        elif phase == "Taper":
            peak_lr = max(long_runs) if long_runs else lr

            if i == 11:  # week 12
                lr = math.floor(peak_lr * 0.70)

            elif i == 12:  # week 13
                lr = math.floor(peak_lr * 0.50)

            lr = lr - (lr % 2)

            long_runs.append(lr)
            prev_lr = lr
            continue

        lr = math.floor(mileage * pct)
        lr = min(lr,20)

        if prev_lr > 0:
            lr = min(lr, prev_lr + 2)

        if lr == 20 and prev_lr == 20:
            lr = 18

        if peak < 50:
            if lr == 20:
                if twenty_count >= 1:
                    lr = 18
                else:
                    twenty_count += 1
        else:
            if lr == 20:
                if twenty_count >= 2:
                    lr = 18
                else:
                    twenty_count += 1

        lr = lr - (lr % 2)

        if lr == prev_lr:
            lr = max(8, lr - 2)

        long_runs.append(lr)
        prev_lr = lr

    return long_runs


# -----------------------------
# VO2
# -----------------------------

def vo2_mileage(peak):

    base = round(peak * 0.10)

    vo2 = []

    for phase in PHASES:

        if phase == "Race":
            vo2.append(0)

        elif phase == "Base":
            vo2.append(round(base*0.8))

        elif phase == "Build":
            vo2.append(base)

        elif phase == "Peak":
            vo2.append(round(base*1.1))

        else:
            vo2.append(round(base*0.7))

    return vo2


# -----------------------------
# TEMPO
# -----------------------------

def tempo_weeks():

    tempo = []

    for i in range(WEEKS):

        if i <= 7 and i % 2 == 0:
            tempo.append(True)
        else:
            tempo.append(False)

    return tempo


# -----------------------------
# SESSION DISTRIBUTION
# -----------------------------

def distribute_runs(mileage, lr, vo2, tempo_flag, runs_per_week):

    if lr == 0:
        return {
            "z2_runs":[3,3,2],
            "tempo":0,
            "vo2":0,
            "lr":0
        }

    tempo_miles = 0

    if tempo_flag:
        tempo_miles = min(6, round(mileage*0.15))

    remaining = mileage - lr - vo2 - tempo_miles

    z2_days = runs_per_week - 2
    if tempo_flag:
        z2_days -= 1

    z2_runs = []

    if z2_days > 0:
        per_day = remaining // z2_days

        for _ in range(z2_days):
            z2_runs.append(per_day)

        leftover = remaining - per_day*z2_days

        for i in range(leftover):
            z2_runs[i] += 1

    return {
        "z2_runs":z2_runs,
        "tempo":tempo_miles,
        "vo2":vo2,
        "lr":lr
    }


# -----------------------------
# BUILD PLAN
# -----------------------------

def build_plan(peak, runs_per_week):

    weekly = generate_weekly_mileage(peak)
    long_runs = calculate_long_runs(weekly, peak)
    vo2 = vo2_mileage(peak)
    tempo = tempo_weeks()

    plan = []

    for i in range(WEEKS):

        sessions = distribute_runs(
            weekly[i],
            long_runs[i],
            vo2[i],
            tempo[i],
            runs_per_week
        )

        plan.append({
            "week":i+1,
            "phase":PHASES[i],
            "mileage":weekly[i],
            "sessions":sessions
        })

    return plan


# -----------------------------
# PRINT
# -----------------------------

def print_plan(plan):

    print("\nMARATHON PLAN\n")

    for week in plan:

        s = week["sessions"]

        print(f"Week {week['week']} | {week['phase']} | Mileage {week['mileage']}")

        if week["phase"] == "Race":
            print("  Z2 Runs:", s["z2_runs"])

        else:
            print("  VO2:", s["vo2"])
            if s["tempo"] > 0:
                print("  Tempo:", s["tempo"])

            print("  Long Run:", s["lr"])
            print("  Z2 Runs:", s["z2_runs"])

        print()


# -----------------------------
# MAIN
# -----------------------------

if __name__ == "__main__":

    peak = 45
    runs_per_week = 6

    plan = build_plan(peak, runs_per_week)

    print_plan(plan)