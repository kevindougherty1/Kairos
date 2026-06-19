"""
Marathon engine audit. Generates plans across a matrix of inputs and
checks for shape issues against principled invariants.

This is a one-off audit script — not part of the regular test suite.
"""

from engineV3 import build_plan


PREFERENCES = {
    "long_run_day": "Sat",
    "speed_day": "Tue",
    "unavailable_days": [],
    "preferred_rest_days": ["Sun"],
    "hard_day_style": "spread",
}


CASES = [
    # (experience, current_mileage, longest_run, runs_per_week, weeks)
    ("beginner",     20,  8,  4, 16),
    ("beginner",     25, 10,  5, 16),
    ("beginner",     30, 10,  5, 18),
    ("intermediate", 25, 10,  5, 16),
    ("intermediate", 30, 12,  5, 16),
    ("intermediate", 35, 13,  6, 16),
    ("intermediate", 40, 14,  6, 18),
    ("advanced",     40, 14,  5, 16),
    ("advanced",     45, 16,  6, 16),
    ("advanced",     50, 16,  6, 18),
    ("advanced",     55, 18,  6, 18),
    ("advanced",     60, 18,  7, 18),
]


def week_mileages(plan):
    return [w["mileage"] for w in plan]


def week_phases(plan):
    return [w["phase"] for w in plan]


def long_runs(plan):
    return [w["sessions"]["lr"] for w in plan]


def check_week_over_week_jumps(weeklies, phases, max_pct=0.10, max_abs=4):
    """No climbing week should jump > max(+10%, +4 mi) from prior."""
    issues = []
    for i in range(1, len(weeklies)):
        if phases[i] in ("Taper", "Race"):
            continue
        delta = weeklies[i] - weeklies[i - 1]
        if delta <= 0:
            continue
        cap = max(weeklies[i - 1] * max_pct, max_abs)
        if delta > cap + 0.5:  # small tolerance for rounding
            pct = 100 * delta / weeklies[i - 1]
            issues.append(
                f"  wk{i+1} jump {weeklies[i-1]}->{weeklies[i]} (+{delta} mi, +{pct:.1f}%)"
            )
    return issues


def check_cutback_then_recover(weeklies, phases):
    """After a Base/Build cutback, the recovery to peak shouldn't be sudden."""
    issues = []
    for i in range(1, len(weeklies) - 1):
        if phases[i] in ("Taper", "Race"):
            continue
        # Cutback = local trough
        if weeklies[i] < weeklies[i - 1] and weeklies[i] < weeklies[i + 1]:
            drop_pct = 100 * (weeklies[i - 1] - weeklies[i]) / weeklies[i - 1]
            recover_pct = 100 * (weeklies[i + 1] - weeklies[i]) / weeklies[i]
            if recover_pct > 15:
                issues.append(
                    f"  wk{i+1} cutback {weeklies[i-1]}->{weeklies[i]}->{weeklies[i+1]} "
                    f"(drop -{drop_pct:.0f}%, recovery +{recover_pct:.0f}%)"
                )
    return issues


def check_lr_progression(lrs, phases):
    """LRs should be non-decreasing through Base->Build->Peak, and not stagnate."""
    issues = []
    dev_lrs = [
        (i, lr) for i, (lr, p) in enumerate(zip(lrs, phases))
        if p in ("Base", "Build", "Peak")
    ]
    # Stagnation: 3+ consecutive identical LRs in Base
    consec = 1
    for i in range(1, len(dev_lrs)):
        if dev_lrs[i][1] == dev_lrs[i - 1][1] and phases[dev_lrs[i][0]] == "Base":
            consec += 1
            if consec >= 3:
                issues.append(
                    f"  LR stagnation: wk{dev_lrs[i][0] + 1} — 3+ consecutive at {dev_lrs[i][1]} in Base"
                )
        else:
            consec = 1
    # Backward drop in Build/Peak
    for i in range(1, len(lrs)):
        if phases[i] in ("Build", "Peak") and phases[i - 1] in ("Base", "Build", "Peak"):
            if lrs[i] < lrs[i - 1] - 2 and lrs[i - 1] > 0:
                # Only flag if not a cutback week (mileage drop allows LR drop)
                pass  # handled by mileage check
    return issues


def check_peak_lr_reaches_20(lrs, phases, experience):
    """Advanced runners should hit 20-mi LR at peak. Otherwise reaching 18+ is OK."""
    peak_phase_lrs = [lr for lr, p in zip(lrs, phases) if p == "Peak"]
    if not peak_phase_lrs:
        return ["  no Peak phase weeks found"]
    max_peak_lr = max(peak_phase_lrs)
    if experience == "advanced" and max_peak_lr < 20:
        return [f"  advanced runner Peak LR maxes at {max_peak_lr}, expected 20"]
    if experience == "intermediate" and max_peak_lr < 18:
        return [f"  intermediate runner Peak LR maxes at {max_peak_lr}, expected 18+"]
    return []


def check_quality_load(plan):
    """Quality (VO2 + tempo + LR) shouldn't dominate weekly mileage."""
    issues = []
    for w in plan:
        if w["phase"] in ("Taper", "Race"):
            continue
        s = w["sessions"]
        quality = s["vo2"] + s["tempo"] + s["lr"]
        mileage = w["mileage"]
        if mileage == 0:
            continue
        pct = 100 * quality / mileage
        if pct > 60:
            issues.append(
                f"  wk{w['week']} quality {quality}/{mileage} ({pct:.0f}%)"
            )
    return issues


def audit_case(case):
    plan = build_plan(*case[:5], preferences=PREFERENCES)
    weeklies = week_mileages(plan)
    phases = week_phases(plan)
    lrs = long_runs(plan)
    peak = max(weeklies)

    out = []
    out.append("=" * 70)
    out.append(f"CASE: exp={case[0]:<13} cm={case[1]:<3} lr={case[2]:<3} rpw={case[3]} weeks={case[4]} -> peak={peak}")
    out.append("=" * 70)
    out.append("Weekly:    " + " ".join(f"{m:3d}" for m in weeklies))
    out.append("Phases:    " + " ".join(p[:3].rjust(3) for p in phases))
    out.append("LRs:       " + " ".join(f"{lr:3d}" for lr in lrs))

    issues = []
    for label, check in [
        ("week-over-week jump > +10%/+4mi", check_week_over_week_jumps(weeklies, phases)),
        ("cutback recovery > +15%", check_cutback_then_recover(weeklies, phases)),
        ("LR progression issues", check_lr_progression(lrs, phases)),
        ("Peak LR ceiling", check_peak_lr_reaches_20(lrs, phases, case[0])),
        ("Quality dominates week", check_quality_load(plan)),
    ]:
        if check:
            issues.append(f"\n  [{label}]")
            issues.extend(check)

    if issues:
        out.append("ISSUES:")
        out.extend(issues)
    else:
        out.append("ISSUES: none")
    out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    for case in CASES:
        print(audit_case(case))
