"""
Assertion-based test suite for the strength engine.

Checks library integrity, prescription invariants, scheduling invariants,
and knob behavior against real running plans from both engines.
Exits non-zero if any assertion fails.
"""
import sys
from half_marathon_engine_main_4plus_v5_7 import build_plan as build_hm_plan
from engineV3 import build_plan as build_marathon_plan
from strength_engine import (
    DAYS,
    EQUIPMENT_ACCESS,
    LEG_REP_CYCLE,
    LIFT_LIBRARY,
    MAX_SETS,
    MIN_SETS,
    PHASE_MAP,
    SPLIT_MIN_FREQUENCY,
    SPLIT_TEMPLATES,
    build_strength_plan,
    classify_running_days,
    day_before,
    lift_region,
    run_day_name,
    swap_options,
)

VALID_PATTERNS = {
    "squat", "hinge", "horizontal_push", "vertical_push", "horizontal_pull",
    "vertical_pull", "carry", "olympic", "plyo", "core", "accessory",
}
VALID_BIAS = {"stretch", "peak", "mid"}
VALID_EQUIPMENT = {"barbell", "dumbbell", "cable", "machine", "bodyweight"}
VALID_DIFFICULTY = {"beginner_safe", "needs_technique", "spotter_recommended"}


class Failure(Exception):
    pass


def check(condition, message):
    if not condition:
        raise Failure(message)


# -----------------------------
# LIBRARY INTEGRITY
# -----------------------------

def test_library_integrity():
    names = [e["name"] for e in LIFT_LIBRARY]
    check(len(names) == len(set(names)), "duplicate lift names in library")
    check(55 <= len(LIFT_LIBRARY) <= 95,
          f"library size {len(LIFT_LIBRARY)} outside curated target")
    for e in LIFT_LIBRARY:
        check(e["pattern"] in VALID_PATTERNS, f"{e['name']}: bad pattern {e['pattern']}")
        check(e["bias"] in VALID_BIAS, f"{e['name']}: bad bias {e['bias']}")
        check(e["difficulty"] in VALID_DIFFICULTY, f"{e['name']}: bad difficulty")
        check(e["equipment"] and all(eq in VALID_EQUIPMENT for eq in e["equipment"]),
              f"{e['name']}: bad equipment {e['equipment']}")
        if e["pattern"] == "accessory":
            check(e["muscle"] is not None, f"{e['name']}: accessory without muscle tag")
        if e["time_based"]:
            check(e["dose"], f"{e['name']}: time_based without dose")
        check(isinstance(e["regression"], bool), f"{e['name']}: regression must be a bool")


def test_swap_coverage():
    # Every lift a full-gym user can be prescribed must have at least one swap.
    for e in LIFT_LIBRARY:
        options = swap_options(e["name"], "barbell")
        check(len(options) >= 1, f"{e['name']}: no swap option at full-gym access")
        check(e["name"] not in options, f"{e['name']}: swap list contains itself")


def test_beginner_swaps_exist_for_technical_lifts():
    # A beginner swapping out a technical lift must get beginner-safe options.
    for e in LIFT_LIBRARY:
        if e["difficulty"] == "beginner_safe" or e["pattern"] in ("olympic", "plyo"):
            continue
        options = swap_options(e["name"], "barbell", "beginner")
        check(len(options) >= 1, f"{e['name']}: no beginner-safe swap at full gym")


# -----------------------------
# PLAN INVARIANTS
# -----------------------------

def hard_days_of(week_schedule):
    hard, easy, rest, lr_day = classify_running_days(week_schedule)
    return hard, lr_day


def assert_week_shape(sp, running_plan, frequency):
    check(len(sp["weeks"]) == len(running_plan),
          f"strength weeks {len(sp['weeks'])} != running weeks {len(running_plan)}")
    for week, running_week in zip(sp["weeks"], running_plan):
        check(week["phase"] == running_week["phase"], "phase mismatch with running plan")
        check(PHASE_MAP[week["phase"]] == week["strength_phase"], "strength_phase mismatch")
        if week["strength_phase"] == "Race":
            check(week["sessions"] == [], "Race week must have no lifting")
            continue
        days = [s["day"] for s in week["sessions"]]
        check(len(days) == len(set(days)), f"week {week['week']}: duplicate strength days")
        check(all(d in DAYS for d in days), f"week {week['week']}: bad day name")
        placed_short = any("could be placed" in w for w in week["warnings"])
        check(len(week["sessions"]) == frequency or placed_short,
              f"week {week['week']}: {len(week['sessions'])} sessions != frequency {frequency}")
        for session in week["sessions"]:
            check(len(session["lifts"]) >= 3, f"week {week['week']}: session too thin")
            session_names = [rx["name"] for rx in session["lifts"]]
            check(len(session_names) == len(set(session_names)),
                  f"week {week['week']}: duplicate lift within session")


def assert_prescriptions(sp):
    for week in sp["weeks"]:
        phase = week["strength_phase"]
        for session in week["sessions"]:
            for rx in session["lifts"]:
                if rx["pattern"] == "plyo":
                    check(phase == "Build", f"plyo outside Build: week {week['week']}")
                    check(rx["sets"] <= 3, "plyo over 3 sets")
                    continue
                check(MIN_SETS <= rx["sets"] <= MAX_SETS,
                      f"week {week['week']} {rx['name']}: sets {rx['sets']} outside bounds")
                if phase == "Deload":
                    check(rx["sets"] == 2, f"Deload sets {rx['sets']} != 2")
                    if rx["rir"] is not None:
                        check(rx["rir"] == "2-3", f"Deload RIR {rx['rir']} != 2-3")
                check(rx["cue"], f"{rx['name']}: missing effort cue")


def assert_plyo_only_leg_heavy(sp):
    leg_heavy_names = {
        t["name"] for templates in SPLIT_TEMPLATES.values() for t in templates if t["leg_heavy"]
    }
    for week in sp["weeks"]:
        for session in week["sessions"]:
            if any(rx["pattern"] == "plyo" for rx in session["lifts"]):
                check(session["name"] in leg_heavy_names or "No Olympic-lift" in " ".join(sp["notes"]),
                      f"plyo in non-leg session {session['name']}")


def assert_stagger_placement(sp, running_plan):
    for week, running_week in zip(sp["weeks"], running_plan):
        if week["strength_phase"] == "Race":
            continue
        hard, lr_day = hard_days_of(running_week["schedule"])
        before_hard = {day_before(d) for d in hard if day_before(d)}
        warned_spill = any("hard running day" in w for w in week["warnings"])
        warned_before = any("day before a hard run" in w for w in week["warnings"])
        for session in week["sessions"]:
            if session["day"] in hard:
                check(warned_spill,
                      f"week {week['week']}: stagger put strength on hard day "
                      f"{session['day']} without warning")
            elif session["day"] in before_hard:
                check(warned_before,
                      f"week {week['week']}: stagger put strength before hard day "
                      f"without warning ({session['day']})")


def assert_leg_heavy_off_lr(sp, running_plan, split):
    leg_heavy_names = {t["name"] for t in SPLIT_TEMPLATES[split] if t["leg_heavy"]}
    for week, running_week in zip(sp["weeks"], running_plan):
        if week["strength_phase"] == "Race":
            continue
        _, lr_day = hard_days_of(running_week["schedule"])
        if lr_day is None:
            continue
        bad_days = {lr_day, day_before(lr_day)} - {None}
        warned = any("adjacent to the long run" in w for w in week["warnings"])
        for session in week["sessions"]:
            if session["name"] in leg_heavy_names and session["day"] in bad_days:
                check(warned,
                      f"week {week['week']}: leg session {session['name']} on "
                      f"{session['day']} (LR {lr_day}) without warning")


def assert_set_progression_within_phase(sp):
    # Non-plyo compound sets should never decrease inside a contiguous
    # engine-phase block (double progression steps up, resets at phase change).
    prev_phase, prev_sets = None, None
    for week in sp["weeks"]:
        if not week["sessions"]:
            prev_phase, prev_sets = None, None
            continue
        week_sets = max(
            rx["sets"] for s in week["sessions"] for rx in s["lifts"]
            if rx["pattern"] != "plyo"
        )
        if week["phase"] == prev_phase and prev_sets is not None:
            check(week_sets >= prev_sets,
                  f"week {week['week']}: sets dropped {prev_sets}->{week_sets} mid-phase")
        prev_phase, prev_sets = week["phase"], week_sets


# -----------------------------
# KNOBS AND VALIDATION
# -----------------------------

def compound_rep_ranges(sp):
    out = set()
    for week in sp["weeks"]:
        if week["strength_phase"] in ("Race", "Deload"):
            continue
        for session in week["sessions"]:
            for rx in session["lifts"]:
                if rx["rir"] is not None and "-" in rx["reps"]:
                    out.add((rx["name"], rx["reps"]))
    return out


def test_emphasis_knob(hm_plan):
    strength = build_strength_plan(
        hm_plan, "advanced", split="upper_lower", frequency=4, equipment="barbell",
        preferences={"emphasis": "strength"},
    )
    compound_names = {e["name"] for e in LIFT_LIBRARY if e["compound"] and not e["time_based"]}
    for name, reps in compound_rep_ranges(strength):
        if name in compound_names:
            check(reps == "3-6", f"strength emphasis: {name} reps {reps} != 3-6")

    hyper = build_strength_plan(
        hm_plan, "advanced", split="upper_lower", frequency=4, equipment="barbell",
        preferences={"emphasis": "hypertrophy"},
    )
    for name, reps in compound_rep_ranges(hyper):
        if name in compound_names:
            check(reps == "8-12", f"hypertrophy emphasis: {name} reps {reps} != 8-12")


def test_recovery_knob(hm_plan):
    fast = build_strength_plan(
        hm_plan, "intermediate", split="ppl", frequency=3, equipment="barbell",
        preferences={"recovery": "fast"},
    )
    slow = build_strength_plan(
        hm_plan, "intermediate", split="ppl", frequency=3, equipment="barbell",
        preferences={"recovery": "slow"},
    )
    for f_week, s_week in zip(fast["weeks"], slow["weeks"]):
        if f_week["strength_phase"] in ("Race", "Deload"):
            continue
        f_sets = [rx["sets"] for s in f_week["sessions"] for rx in s["lifts"] if rx["pattern"] != "plyo"]
        s_sets = [rx["sets"] for s in s_week["sessions"] for rx in s["lifts"] if rx["pattern"] != "plyo"]
        check(max(f_sets) <= MAX_SETS and min(s_sets) >= MIN_SETS, "recovery knob broke set bounds")
        check(max(f_sets) > max(s_sets),
              f"week {f_week['week']}: fast recovery sets {max(f_sets)} "
              f"not above slow {max(s_sets)}")
    # Deload ignores the knob entirely.
    for week in fast["weeks"]:
        if week["strength_phase"] == "Deload":
            for session in week["sessions"]:
                for rx in session["lifts"]:
                    if rx["pattern"] != "plyo":
                        check(rx["sets"] == 2, "fast recovery inflated the deload")


def test_beginner_gets_safe_lifts(hm_plan_beginner):
    sp = build_strength_plan(hm_plan_beginner, "beginner", split="full_body",
                             frequency=3, equipment="barbell")
    safe_names = {e["name"] for e in LIFT_LIBRARY if e["difficulty"] == "beginner_safe"}
    flagged = " ".join(sp["notes"])
    for week in sp["weeks"]:
        for session in week["sessions"]:
            for rx in session["lifts"]:
                check(rx["name"] in safe_names or rx["name"] in flagged,
                      f"beginner prescribed {rx['name']} without a difficulty note")


def test_validation_errors(hm_plan):
    cases = [
        dict(experience="elite"),
        dict(split="bro_split"),
        dict(equipment="kettlebell"),
        dict(frequency=1),
        dict(frequency=7),
        dict(split="ppl", frequency=2),
        dict(preferences={"scheduling_style": "chaos"}),
        dict(preferences={"recovery": "instant"}),
        dict(preferences={"emphasis": "cardio"}),
        dict(pattern_equipment={"not_a_pattern": "barbell"}),
        dict(pattern_equipment={"squat": "kettlebell"}),
        dict(region_reps={"forearms": "6-8"}),
        dict(region_reps={"chest": "5-5"}),
    ]
    for overrides in cases:
        kwargs = dict(experience="intermediate", split="full_body",
                      frequency=3, equipment="dumbbell", preferences=None)
        kwargs.update(overrides)
        try:
            build_strength_plan(hm_plan, **kwargs)
        except ValueError:
            continue
        raise Failure(f"expected ValueError for {overrides}")


def test_olympic_bodyweight_fallback(hm_plan):
    sp = build_strength_plan(hm_plan, "intermediate", split="olympic_focused",
                             frequency=2, equipment="bodyweight")
    check(any("substituting jump work" in n for n in sp["notes"]),
          "olympic+bodyweight: missing substitution note")
    for week in sp["weeks"]:
        for session in week["sessions"]:
            check(len(session["lifts"]) >= 3, "olympic bodyweight session too thin")


def _phase_blocks(sp):
    """Group a strength plan's weeks into contiguous same-phase blocks."""
    blocks = []
    for week in sp["weeks"]:
        if not blocks or blocks[-1][0] != week["phase"]:
            blocks.append((week["phase"], []))
        blocks[-1][1].append(week)
    return blocks


def _session_lift_names(week, session_name):
    for session in week["sessions"]:
        if session["name"] == session_name:
            return [rx["name"] for rx in session["lifts"]]
    return None


def test_lift_rotates_across_phase_blocks(hm_plan):
    # Barbell = full gym access = richest candidate pools, so rotation has
    # real room to work with (full_body's squat/hinge/push/pull slots all
    # resolve to multi-candidate top tiers at this equipment tier).
    sp = build_strength_plan(hm_plan, "advanced", split="full_body", frequency=2,
                             equipment="barbell")
    blocks = _phase_blocks(sp)
    non_race = [b for b in blocks if b[1][0]["strength_phase"] != "Race"]
    check(len(non_race) >= 2, "need at least 2 non-Race phase blocks to test rotation")

    picks_per_block = []
    for _, weeks in non_race:
        names = _session_lift_names(weeks[0], "Full Body A")
        check(names is not None, "Full Body A not scheduled in a non-Race block")
        picks_per_block.append(tuple(names))

    check(len(set(picks_per_block)) >= 2,
          f"Full Body A lifts identical across every phase block: {picks_per_block}")


def test_lift_stable_within_phase_block(hm_plan):
    sp = build_strength_plan(hm_plan, "advanced", split="full_body", frequency=2,
                             equipment="barbell")
    for phase, weeks in _phase_blocks(sp):
        if weeks[0]["strength_phase"] == "Race":
            continue
        first = _session_lift_names(weeks[0], "Full Body A")
        for week in weeks[1:]:
            names = _session_lift_names(week, "Full Body A")
            if names is None:
                continue  # session cycle may not land "Full Body A" every week
            check(names == first,
                  f"{phase} week {week['week']}: Full Body A lifts changed mid-block "
                  f"{first} -> {names}")


def test_override_honored(hm_plan):
    # Whatever alternative the engine offers for Full Body A's squat slot,
    # pinning it as an override should win out over rotation for every week.
    baseline = build_strength_plan(hm_plan, "advanced", split="full_body", frequency=2,
                                   equipment="barbell")
    week1_squat = next(rx for rx in baseline["weeks"][0]["sessions"][0]["lifts"]
                        if rx["pattern"] == "squat")
    check(week1_squat["alternatives"], "expected at least one squat alternative at barbell tier")
    alt_name = week1_squat["alternatives"][0]

    sp = build_strength_plan(hm_plan, "advanced", split="full_body", frequency=2,
                             equipment="barbell",
                             overrides={week1_squat["slot_key"]: alt_name})
    for week in sp["weeks"]:
        if week["strength_phase"] == "Race":
            continue
        fba = next(s for s in week["sessions"] if s["name"] == "Full Body A")
        squat_rx = next(rx for rx in fba["lifts"] if rx["pattern"] == "squat")
        check(squat_rx["name"] == alt_name,
              f"week {week['week']}: override not honored, got {squat_rx['name']}")


def test_override_falls_back_when_invalid(hm_plan):
    # "Back Squat" is barbell-only; pinning it while equipment is bodyweight
    # can't resolve, so the slot should fall back to an auto-pick with a warning.
    key = "Full Body A|squat|compound|"
    sp = build_strength_plan(hm_plan, "advanced", split="full_body", frequency=2,
                             equipment="bodyweight",
                             overrides={key: "Back Squat"})
    fba = next(s for s in sp["weeks"][0]["sessions"] if s["name"] == "Full Body A")
    squat_rx = next(rx for rx in fba["lifts"] if rx["pattern"] == "squat")
    check(squat_rx["name"] != "Back Squat", "invalid override should not have been honored")
    check(any("using the default pick instead" in n for n in sp["notes"]),
          "expected a fallback warning when an override doesn't resolve")


def test_pattern_equipment_preference(hm_plan):
    # Squat pattern, machine preference at full barbell access: every week's
    # squat pick should be a machine lift (Leg Press/Hack Squat), never a
    # barbell squat, even though barbell squats would otherwise win by default.
    sp = build_strength_plan(hm_plan, "advanced", split="full_body", frequency=2,
                             equipment="barbell",
                             pattern_equipment={"squat": "machine"})
    for week in sp["weeks"]:
        if week["strength_phase"] == "Race":
            continue
        fba = next(s for s in week["sessions"] if s["name"] == "Full Body A")
        squat_rx = next(rx for rx in fba["lifts"] if rx["pattern"] == "squat")
        entry = next(e for e in LIFT_LIBRARY if e["name"] == squat_rx["name"])
        check("machine" in entry["equipment"],
              f"week {week['week']}: squat pick {squat_rx['name']} isn't a machine lift")


def _picks_per_block(sp, predicate):
    """First-week pick for each contiguous phase block, for matching lifts."""
    out = []
    for _, weeks in _phase_blocks(sp):
        if weeks[0]["strength_phase"] == "Race":
            continue
        for session in weeks[0]["sessions"]:
            for rx in session["lifts"]:
                entry = next(e for e in LIFT_LIBRARY if e["name"] == rx["name"])
                if predicate(entry):
                    out.append(rx["name"])
    return out


def test_accessory_slots_rotate(hm_plan):
    # Rear delts and abductors each have exactly one lift at their best
    # equipment tier, so they can only rotate if the tier widens.
    sp = build_strength_plan(hm_plan, "advanced", split="ppl", frequency=3,
                             equipment="barbell")
    for muscle in ("rear_delts", "abductors"):
        picks = _picks_per_block(sp, lambda e, m=muscle: e["muscle"] == m)
        check(len(picks) >= 2, f"{muscle}: expected picks in multiple blocks, got {picks}")
        check(len(set(picks)) >= 2,
              f"{muscle}: same lift in every phase block ({picks[0]}) — not rotating")


def test_widening_keeps_compounds_off_regressions(hm_plan):
    # Widening the rotation tier must not drop a full-gym lifter into a
    # bodyweight/assisted regression of a main compound (e.g. Pike Push-Up
    # for vertical push). Small isolations may cross tiers; compounds may not.
    sp = build_strength_plan(hm_plan, "advanced", split="ppl", frequency=3,
                             equipment="barbell")
    banned = {"Pike Push-Up", "Inverted Row", "Bodyweight Squat", "Push-Up"}
    for week in sp["weeks"]:
        for session in week["sessions"]:
            for rx in session["lifts"]:
                check(rx["name"] not in banned,
                      f"week {week['week']}: full-gym advanced plan prescribed "
                      f"{rx['name']} — rotation reached into a regression")


def _all_lift_names(sp):
    return {rx["name"] for w in sp["weeks"] for s in w["sessions"] for rx in s["lifts"]}


def test_beginner_hinge_isolation_rotates(hm_plan_beginner):
    # Seated Leg Curl was once the only beginner-safe stretch-biased hinge
    # isolation, which froze the slot for a whole plan. Assisted Nordic Curl
    # gives it a partner without displacing real Nordics for advanced (it is
    # regression-tagged, so it stays out of their rotation).
    sp = build_strength_plan(hm_plan_beginner, "beginner", split="ppl", frequency=3,
                             equipment="barbell")
    picks = _picks_per_block(
        sp, lambda e: e["pattern"] == "hinge" and not e["compound"]
    )
    check(len(set(picks)) >= 2,
          f"beginner hinge isolation slot is static: {picks}")


def test_regressions_stay_out_of_rotation(hm_plan, hm_plan_beginner):
    regressions = {e["name"] for e in LIFT_LIBRARY if e["regression"]}
    check(regressions, "expected at least one lift tagged as a regression")

    # Advanced, full gym: never rotated into an assisted variant.
    adv = build_strength_plan(hm_plan, "advanced", split="ppl", frequency=3,
                              equipment="barbell")
    leaked = _all_lift_names(adv) & regressions
    check(not leaked, f"advanced plan rotated into regression lift(s): {sorted(leaked)}")

    # Beginners keep them — assisted work is the progression path for them,
    # and swap_options still offers them to everyone regardless.
    check("Assisted Pull-Up" in swap_options("Lat Pulldown", "barbell"),
          "regression tag should not remove the lift from swap options")
    bgn = build_strength_plan(hm_plan_beginner, "beginner", split="ppl", frequency=3,
                              equipment="barbell")
    check(_all_lift_names(bgn) & regressions,
          "beginner plan should still be able to use assisted variants")


REGION_RX = {"chest": "6-8", "back": "6-8", "shoulders": "6-8", "arms": "8-12"}


def _rep_bearing_lifts(week):
    """Lifts whose reps come from the rep tables (not plyo / time-based doses)."""
    for session in week["sessions"]:
        for rx in session["lifts"]:
            if rx["pattern"] == "plyo" or "-" not in rx["reps"]:
                continue
            entry = next(e for e in LIFT_LIBRARY if e["name"] == rx["name"])
            if entry["time_based"]:
                continue
            yield rx, entry


def test_region_rep_ranges(hm_plan):
    sp = build_strength_plan(hm_plan, "advanced", split="ppl", frequency=3,
                             equipment="barbell", region_reps=REGION_RX)
    seen = set()
    for week in sp["weeks"]:
        if week["strength_phase"] in ("Race", "Deload"):
            continue
        for rx, entry in _rep_bearing_lifts(week):
            region = lift_region(entry)
            if region in REGION_RX:
                check(rx["reps"] == REGION_RX[region],
                      f"week {week['week']} {rx['name']} ({region}): "
                      f"reps {rx['reps']} != {REGION_RX[region]}")
                seen.add(region)
    check(seen >= {"chest", "back", "shoulders", "arms"},
          f"expected all configured regions to appear in a PPL plan, saw {seen}")


def test_region_reps_vary_legs(hm_plan):
    sp = build_strength_plan(hm_plan, "advanced", split="full_body", frequency=2,
                             equipment="barbell", region_reps={"legs": "vary"})
    # Distinct phase blocks should walk LEG_REP_CYCLE in order.
    by_block = []
    for phase, weeks in _phase_blocks(sp):
        if weeks[0]["strength_phase"] in ("Race", "Deload"):
            continue
        leg_reps = {rx["reps"] for rx, entry in _rep_bearing_lifts(weeks[0])
                    if lift_region(entry) == "legs"}
        check(len(leg_reps) == 1,
              f"{phase}: legs should share one rep range, got {leg_reps}")
        by_block.append(leg_reps.pop())
    expected = [f"{lo}-{hi}" for lo, hi in LEG_REP_CYCLE][:len(by_block)]
    check(by_block == expected, f"leg cycle {by_block} != {expected}")


def test_region_reps_exempt_deload(hm_plan):
    sp = build_strength_plan(hm_plan, "advanced", split="ppl", frequency=3,
                             equipment="barbell",
                             region_reps=dict(REGION_RX, legs="vary"))
    phase_ranges = {"8-10", "10-12"}  # PHASE_RX["Deload"] compound / isolation
    saw_deload = False
    for week in sp["weeks"]:
        if week["strength_phase"] != "Deload":
            continue
        saw_deload = True
        for rx, entry in _rep_bearing_lifts(week):
            check(rx["reps"] in phase_ranges,
                  f"Deload week {week['week']} {rx['name']}: reps {rx['reps']} "
                  f"not from the phase table {phase_ranges}")
    check(saw_deload, "plan had no Deload week to check")


def test_pattern_equipment_no_candidates_falls_back(hm_plan):
    # No barbell vertical-pull lift exists in the library; the preference
    # should just be a silent no-op, not an error or a stuck plan.
    sp = build_strength_plan(hm_plan, "intermediate", split="upper_lower", frequency=4,
                             equipment="barbell",
                             pattern_equipment={"vertical_pull": "barbell"})
    check(len(sp["weeks"]) == len(hm_plan), "plan should still build normally")


def test_split_cycle_continuity(hm_plan):
    # PPL at 4x/week must continue the cycle across weeks, not restart it.
    sp = build_strength_plan(hm_plan, "advanced", split="ppl", frequency=4,
                             equipment="barbell")
    cycle = [t["name"] for t in SPLIT_TEMPLATES["ppl"]]
    expected = None
    for week in sp["weeks"]:
        if week["strength_phase"] == "Race":
            continue
        # sessions are chronological, but cycle order may be swapped for
        # leg-day placement; check multiset per week instead
        got = sorted(s["name"] for s in week["sessions"])
        if expected is None:
            idx = 0
        want = sorted(cycle[(idx + k) % len(cycle)] for k in range(4))
        check(got == want, f"week {week['week']}: cycle {got} != {want}")
        idx += 4
        expected = True


# -----------------------------
# RUNNER
# -----------------------------

def main():
    _, hm_int = build_hm_plan(experience="intermediate", current_mileage=35,
                              recent_longest_run=10, runs_per_week=5, weeks=12)
    _, hm_bgn = build_hm_plan(experience="beginner", current_mileage=20,
                              recent_longest_run=8, runs_per_week=4, weeks=12)
    _, hm_adv = build_hm_plan(experience="advanced", current_mileage=45,
                              recent_longest_run=12, runs_per_week=6, weeks=12)
    mar_prefs = {"long_run_day": "Sat", "speed_day": "Tue"}
    mar_bgn = build_marathon_plan(experience="beginner", current_mileage=22,
                                  longest_run=10, runs_per_week=5, weeks=14,
                                  preferences=mar_prefs)
    mar_adv = build_marathon_plan(experience="advanced", current_mileage=45,
                                  longest_run=16, runs_per_week=6, weeks=16,
                                  preferences=mar_prefs)

    matrix = [
        # (label, running_plan, experience, split, frequency, equipment, style)
        ("hm-int ppl3 bb stack", hm_int, "intermediate", "ppl", 3, "barbell", "stack"),
        ("hm-int ul4 db stagger", hm_int, "intermediate", "upper_lower", 4, "dumbbell", "stagger"),
        ("hm-bgn fb2 bw stagger", hm_bgn, "beginner", "full_body", 2, "bodyweight", "stagger"),
        ("hm-adv pl3 bb stack", hm_adv, "advanced", "powerlifting_focused", 3, "barbell", "stack"),
        ("hm-adv oly2 bb stack", hm_adv, "advanced", "olympic_focused", 2, "barbell", "stack"),
        ("mar-bgn fb3 db stagger", mar_bgn, "beginner", "full_body", 3, "dumbbell", "stagger"),
        ("mar-adv ppl5 bb stack", mar_adv, "advanced", "ppl", 5, "barbell", "stack"),
        ("mar-adv ul6 bb stagger", mar_adv, "advanced", "upper_lower", 6, "barbell", "stagger"),
    ]

    checks = [
        ("library integrity", test_library_integrity),
        ("swap coverage", test_swap_coverage),
        ("beginner swaps for technical lifts", test_beginner_swaps_exist_for_technical_lifts),
    ]

    failures = []
    for label, fn in checks:
        try:
            fn()
            print(f"PASS  {label}")
        except Failure as e:
            failures.append((label, str(e)))
            print(f"FAIL  {label}: {e}")

    for label, running_plan, exp, split, freq, equip, style in matrix:
        try:
            sp = build_strength_plan(
                running_plan, exp, split=split, frequency=freq, equipment=equip,
                preferences={"scheduling_style": style},
            )
            assert_week_shape(sp, running_plan, freq)
            assert_prescriptions(sp)
            assert_plyo_only_leg_heavy(sp)
            assert_set_progression_within_phase(sp)
            if style == "stagger":
                assert_stagger_placement(sp, running_plan)
            assert_leg_heavy_off_lr(sp, running_plan, split)
            print(f"PASS  {label}")
        except Failure as e:
            failures.append((label, str(e)))
            print(f"FAIL  {label}: {e}")

    extra = [
        ("emphasis knob", lambda: test_emphasis_knob(hm_int)),
        ("recovery knob", lambda: test_recovery_knob(hm_int)),
        ("beginner safe lifts", lambda: test_beginner_gets_safe_lifts(hm_bgn)),
        ("validation errors", lambda: test_validation_errors(hm_int)),
        ("olympic bodyweight fallback", lambda: test_olympic_bodyweight_fallback(hm_int)),
        ("split cycle continuity", lambda: test_split_cycle_continuity(hm_int)),
        ("lift rotates across phase blocks", lambda: test_lift_rotates_across_phase_blocks(hm_int)),
        ("lift stable within phase block", lambda: test_lift_stable_within_phase_block(hm_int)),
        ("override honored", lambda: test_override_honored(hm_int)),
        ("override falls back when invalid", lambda: test_override_falls_back_when_invalid(hm_int)),
        ("pattern equipment preference", lambda: test_pattern_equipment_preference(hm_int)),
        ("pattern equipment no candidates falls back",
         lambda: test_pattern_equipment_no_candidates_falls_back(hm_int)),
        ("accessory slots rotate", lambda: test_accessory_slots_rotate(hm_int)),
        ("regressions stay out of rotation",
         lambda: test_regressions_stay_out_of_rotation(hm_int, hm_bgn)),
        ("beginner hinge isolation rotates",
         lambda: test_beginner_hinge_isolation_rotates(hm_bgn)),
        ("widening keeps compounds off regressions",
         lambda: test_widening_keeps_compounds_off_regressions(hm_int)),
        ("region rep ranges", lambda: test_region_rep_ranges(hm_int)),
        ("region reps vary legs", lambda: test_region_reps_vary_legs(hm_int)),
        ("region reps exempt deload", lambda: test_region_reps_exempt_deload(hm_int)),
    ]
    for label, fn in extra:
        try:
            fn()
            print(f"PASS  {label}")
        except Failure as e:
            failures.append((label, str(e)))
            print(f"FAIL  {label}: {e}")

    print()
    total = len(checks) + len(matrix) + len(extra)
    if failures:
        print(f"{len(failures)}/{total} FAILED")
        sys.exit(1)
    print(f"ALL {total} PASS")


if __name__ == "__main__":
    main()
