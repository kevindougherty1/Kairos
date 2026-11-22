r"""Read-only probe of the two Kairos running engines (see portal/ENGINES.md).

Usage (from the repo root): .venv\Scripts\python.exe -B portal/scripts/probe_engines.py
Imports the engines and calls build_plan(); writes nothing.
"""
import copy, json, os, re, sys, itertools
REPO = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
import engineV3 as M
import half_marathon_engine_main_4plus_v5_7 as H

LABEL = re.compile(r"^(.+?) \((\d+)\)$")

def m_sched_miles(week):
    tot = 0
    for v in week["schedule"].values():
        mm = LABEL.match(v)
        if mm:
            tot += int(mm.group(2))
    return tot

def h_sched_miles(week):
    return sum(item["miles"] or 0 for item in week["schedule"].values())

M_PREF = {"long_run_day": "Sat", "speed_day": "Tue", "unavailable_days": [], "preferred_rest_days": ["Sun"]}
H_PREF = {"long_run_day": "Sat", "quality_day": "Tue", "unavailable_days": [], "preferred_rest_days": ["Sun"]}

def run_m(exp, cm, lr, rpw, wk, pref=None):
    return M.build_plan(exp, cm, lr, rpw, wk, copy.deepcopy(pref or M_PREF))

def run_h(exp, cm, lr, rpw, wk, pref=None):
    return H.build_plan(exp, cm, lr, rpw, wk, copy.deepcopy(pref or H_PREF))

print("== 1. Determinism + JSON + input mutation")
for name, fn, pref in [("marathon", M.build_plan, M_PREF), ("hm", H.build_plan, H_PREF)]:
    p1 = copy.deepcopy(pref); p2 = copy.deepcopy(pref)
    a = fn("intermediate", 30, 12, 5, 16, p1)
    b = fn("intermediate", 30, 12, 5, 16, p2)
    ja, jb = json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True)
    print(f"  {name}: identical={ja == jb} json_ok=True bytes={len(ja)} prefs_mutated={p1 != pref}")

print("== 2. Output shape")
mp = run_m("intermediate", 30, 12, 6, 16)
print("  marathon type:", type(mp).__name__, "len", len(mp), "week keys:", list(mp[0].keys()))
print("  marathon sessions keys:", list(mp[0]["sessions"].keys()))
labels = sorted({LABEL.sub(r"\1 (n)", v) for w in mp for v in w["schedule"].values()})
print("  marathon schedule labels:", labels)
peak, hp = run_h("intermediate", 30, 10, 5, 12)
print("  hm returns tuple (peak, plan); peak", peak, "len", len(hp), "week keys:", list(hp[0].keys()))
print("  hm sessions keys:", list(hp[0]["sessions"].keys()), "primary:", hp[0]["primary"])
names = sorted({i["name"] for w in hp for i in w["schedule"].values()})
print("  hm schedule names:", names)
print("  hm plan_warnings shared object across weeks:", all(w["plan_warnings"] is hp[0]["plan_warnings"] for w in hp))
print("  hm sessions['primary'] is week['primary']:", hp[0]["sessions"]["primary"] is hp[0]["primary"])

print("== 3. Schedule sum vs stated weekly mileage (full input matrix)")
exps = ["beginner", "intermediate", "advanced"]
for name in ["marathon", "hm"]:
    weeks_range = range(12, 25, 2) if name == "marathon" else range(8, 21, 2)
    n_plans = n_weeks = mismatch = 0; examples = []; warn_counts = {}; errors = []
    for exp, cm, rpw, wk in itertools.product(exps, range(10, 71, 5), [4, 5, 6], weeks_range):
        lr = max(4, round(cm * 0.33))
        try:
            plan = run_m(exp, cm, lr, rpw, wk) if name == "marathon" else run_h(exp, cm, lr, rpw, wk)[1]
        except Exception as e:
            errors.append((exp, cm, rpw, wk, repr(e))); continue
        n_plans += 1
        for w in plan:
            n_weeks += 1
            s = m_sched_miles(w) if name == "marathon" else h_sched_miles(w)
            if w["phase"] != "Race" and s != w["mileage"]:
                mismatch += 1
                if len(examples) < 4:
                    examples.append(f"{exp} cm{cm} {rpw}d {wk}wk wk{w['week']} {w['phase']}: stated {w['mileage']} sched {s}")
            for x in w["warnings"]:
                k = re.sub(r"\d+", "N", x)
                warn_counts[k] = warn_counts.get(k, 0) + 1
    print(f"  {name}: plans={n_plans} weeks={n_weeks} non-race weeks where schedule != mileage: {mismatch}")
    for e in examples: print("     e.g.", e)
    print(f"  {name} warnings seen:", json.dumps(warn_counts, indent=None))
    print(f"  {name} errors in matrix: {len(errors)}", errors[:3])

print("== 4. Race week")
print("  marathon race week:", mp[-1]["mileage"], mp[-1]["schedule"])
print("  hm race week:", hp[-1]["mileage"], {d: i["name"] for d, i in hp[-1]["schedule"].items() if i["name"] != "Rest"})

print("== 5. Edge inputs")
def probe(label, thunk):
    try:
        r = thunk()
        plan = r[1] if isinstance(r, tuple) else r
        print(f"  OK   {label}: {len(plan)} weeks, phases={[w['phase'][:3] for w in plan]}")
    except Exception as e:
        print(f"  FAIL {label}: {type(e).__name__}: {e}")
for wk in [1, 3, 4, 5, 6, 8, 10, 30]:
    probe(f"marathon weeks={wk}", lambda wk=wk: run_m("intermediate", 30, 12, 5, wk))
for wk in [1, 3, 4, 5, 6, 30]:
    probe(f"hm weeks={wk}", lambda wk=wk: run_h("intermediate", 25, 8, 5, wk))
probe("marathon exp='Beginner' (case)", lambda: run_m("Beginner", 30, 12, 5, 16))
probe("hm exp='expert'", lambda: run_h("expert", 30, 12, 5, 12))
probe("marathon rpw=3", lambda: run_m("intermediate", 30, 12, 3, 16))
probe("hm rpw=7", lambda: run_h("intermediate", 30, 12, 7, 12))
probe("marathon current_mileage=0", lambda: run_m("beginner", 0, 0, 4, 16))
probe("hm current_mileage=0", lambda: run_h("beginner", 0, 0, 4, 12))
probe("marathon cm=150 lr=30", lambda: run_m("advanced", 150, 30, 6, 18))
probe("hm cm=150 lr=30", lambda: run_h("advanced", 150, 30, 6, 12))
probe("marathon float cm=32.5", lambda: run_m("intermediate", 32.5, 12, 5, 16))
probe("marathon prefs missing speed_day", lambda: M.build_plan("intermediate", 30, 12, 5, 16, {"long_run_day": "Sat"}))
probe("marathon long_run_day=None (app.py default)", lambda: M.build_plan("intermediate", 30, 12, 5, 16, {"long_run_day": None, "speed_day": None}))
probe("marathon day='Saturday'", lambda: run_m("intermediate", 30, 12, 5, 16, {**M_PREF, "long_run_day": "Saturday"}))
probe("hm prefs=None (defaults)", lambda: H.build_plan("intermediate", 25, 8, 5, 12))
probe("hm speed_day key only", lambda: run_h("intermediate", 25, 8, 5, 12, {"long_run_day": "Sun", "speed_day": "Wed"}))

def warns(label, plan):
    ws = sorted({x for w in plan for x in w["warnings"]})
    print(f"  {label}: {ws}")
print("== 6. Preference conflicts -> warnings, not errors")
warns("marathon speed==LR day", run_m("intermediate", 30, 12, 5, 16, {**M_PREF, "speed_day": "Sat"}))
warns("marathon LR day unavailable", run_m("intermediate", 30, 12, 5, 16, {**M_PREF, "unavailable_days": ["Sat"]}))
warns("marathon 3 days unavailable, 6d", run_m("intermediate", 40, 14, 6, 16, {**M_PREF, "unavailable_days": ["Mon", "Wed", "Fri"]}))
warns("hm 3 days unavailable, 6d", run_h("intermediate", 40, 12, 6, 12, {**H_PREF, "unavailable_days": ["Mon", "Wed", "Fri"]})[1])
warns("hm over-qualified plan_warnings", [{"warnings": run_h("intermediate", 60, 14, 5, 12)[1][0]["plan_warnings"]}])
