"""
Assertion-based test suite for the half marathon engine.

Runs each test case through build_plan() and checks structural invariants.
The full plan output is still written to engine_tests.txt for visual review.
Exits non-zero if any assertion fails.
"""
import io
import contextlib
import sys
from half_marathon_engine_main_4plus_v5_7 import build_plan, print_plan, lr_cap

TESTS = [
    # (experience, current_mileage, recent_longest_run, runs_per_week, weeks)
    ("beginner",      20,  8, 4, 12),
    ("beginner",      30, 10, 5, 12),
    ("intermediate",  25,  8, 5, 12),
    ("intermediate",  35, 10, 5, 12),
    ("intermediate",  40, 12, 6, 12),
    ("advanced",      40, 10, 5, 12),
    ("advanced",      45, 12, 5, 12),
    ("advanced",      55, 14, 6, 12),
]

PHASE_ORDER = ["Base", "Build", "Specific", "Taper", "Race"]


class Failure(Exception):
    pass


def check(condition, message):
    if not condition:
        raise Failure(message)


def assert_phase_order(plan, exp, rpw):
    seen = []
    for w in plan:
        if not seen or seen[-1] != w["phase"]:
            seen.append(w["phase"])
    for phase in seen:
        check(phase in PHASE_ORDER, f"unknown phase: {phase}")
    canonical = [p for p in PHASE_ORDER if p in seen]
    check(seen == canonical, f"phase order {seen} != canonical {canonical}")


def assert_race_week(plan, exp, rpw):
    race = [w for w in plan if w["phase"] == "Race"]
    check(len(race) == 1, f"expected 1 Race week, got {len(race)}")
    check(race[0] is plan[-1], "Race week must be last")
    check(race[0]["mileage"] == 6, f"Race week mileage={race[0]['mileage']}, expected 6")


def assert_taper_present(plan, exp, rpw):
    check(any(w["phase"] == "Taper" for w in plan), "expected at least 1 Taper week")


def assert_schedule_sums(plan, exp, rpw):
    for w in plan:
        if w["phase"] == "Race":
            continue  # race day miles=0 but actual race is 13.1; not training mileage
        s = sum(item.get("miles") or 0 for item in w["schedule"].values())
        check(s == w["mileage"],
              f"week {w['week']} ({w['phase']}): schedule sum {s} != mileage {w['mileage']}")


def assert_no_negatives(plan, exp, rpw):
    for w in plan:
        check(w["mileage"] >= 0, f"week {w['week']}: negative mileage {w['mileage']}")
        for day, item in w["schedule"].items():
            m = item.get("miles") or 0
            check(m >= 0, f"week {w['week']} {day}: negative miles {m}")


def assert_lr_within_cap(plan, exp, rpw):
    cap = lr_cap(exp, rpw)
    for w in plan:
        if w["phase"] == "Race":
            continue
        check(w["lr"] <= cap,
              f"week {w['week']} ({w['phase']}): LR {w['lr']} > cap {cap}")


def assert_specific_geq_build(plan, exp, rpw):
    build = [w["lr"] for w in plan if w["phase"] == "Build"]
    spec = [w["lr"] for w in plan if w["phase"] == "Specific"]
    if build and spec:
        check(max(spec) >= max(build),
              f"max Specific LR {max(spec)} < max Build LR {max(build)}")


def assert_taper_descends(plan, exp, rpw):
    tapers = [w["lr"] for w in plan if w["phase"] == "Taper"]
    for a, b in zip(tapers, tapers[1:]):
        check(a > b, f"taper LRs not strictly descending: {tapers}")


def assert_running_days(plan, exp, rpw):
    for w in plan:
        if w["phase"] == "Race":
            continue
        runs = sum(1 for item in w["schedule"].values() if item["name"] != "Rest")
        check(runs == rpw,
              f"week {w['week']} ({w['phase']}): {runs} running days, expected {rpw}")


def assert_peak_consistent(plan, exp, rpw):
    declared = plan[0]["peak_mileage"]
    actual = max(w["mileage"] for w in plan if w["phase"] != "Race")
    check(actual == declared,
          f"actual peak {actual} != declared peak_mileage {declared}")


ASSERTIONS = [
    ("phase order",                       assert_phase_order),
    ("race week structure",               assert_race_week),
    ("taper present",                     assert_taper_present),
    ("schedule sums match weekly mileage", assert_schedule_sums),
    ("no negative numbers",               assert_no_negatives),
    ("LR within cap",                     assert_lr_within_cap),
    ("Specific peak LR >= Build peak LR", assert_specific_geq_build),
    ("taper LRs strictly descend",        assert_taper_descends),
    ("running days match runs_per_week",  assert_running_days),
    ("declared peak matches actual peak", assert_peak_consistent),
]


def main():
    out = open("engine_tests.txt", "w")
    total_passed = 0
    total_failed = 0
    failures = []  # (test, assertion_name, message)

    for test in TESTS:
        exp, current, recent_lr, rpw, weeks = test
        peak, plan = build_plan(
            experience=exp,
            current_mileage=current,
            recent_longest_run=recent_lr,
            runs_per_week=rpw,
            weeks=weeks,
        )

        out.write(f"\n{'='*60}\n")
        out.write(f"TEST: {test}\n")
        out.write(f"{'='*60}\n")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            print_plan(peak, plan)
        out.write(buf.getvalue())

        passed = 0
        failed = 0
        for name, fn in ASSERTIONS:
            try:
                fn(plan, exp, rpw)
                passed += 1
            except Failure as e:
                failed += 1
                failures.append((test, name, str(e)))

        total_passed += passed
        total_failed += failed
        status = "OK" if failed == 0 else f"{failed} FAIL"
        print(f"{str(test):42}  {passed}/{passed + failed} passed  [{status}]")

    out.close()

    print(f"\n{'='*60}")
    print(f"Total assertions: {total_passed + total_failed}  "
          f"passed: {total_passed}  failed: {total_failed}")

    if failures:
        print(f"\nFailures:")
        for test, name, msg in failures:
            print(f"  {test}")
            print(f"    {name}: {msg}")

    print(f"\nFull plan output: engine_tests.txt")
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
