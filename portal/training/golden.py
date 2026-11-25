"""
Golden-output snapshots of the two running engines (brief §4.7: regression tests before integrating).

A fixed input matrix is run through each engine and the JSON output is committed under
training/golden/. The test suite regenerates the output and compares it byte for byte, so any change
in engine behaviour shows up as a failing test with the first differing week.

After an INTENDED engine change, refresh the snapshots and commit them with the change:
    ..\\.venv\\Scripts\\python.exe manage.py engine_golden --update
"""

import copy
import json
from pathlib import Path

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"

# (experience, current_mileage, longest_run, runs_per_week, weeks); the engines' own test/audit matrices
HM_CASES = [
    ("beginner", 20, 8, 4, 12), ("intermediate", 25, 8, 4, 12), ("advanced", 30, 10, 4, 12),
    ("beginner", 30, 10, 5, 12), ("intermediate", 25, 8, 5, 12), ("intermediate", 30, 10, 5, 12),
    ("intermediate", 35, 10, 5, 12), ("intermediate", 40, 12, 5, 12), ("intermediate", 40, 12, 6, 12),
    ("intermediate", 50, 14, 6, 12), ("advanced", 40, 10, 5, 12), ("advanced", 45, 12, 5, 12),
    ("advanced", 50, 14, 5, 12), ("advanced", 55, 14, 6, 12),
    # portal range edges (8 and 20 weeks)
    ("beginner", 15, 6, 4, 8), ("intermediate", 30, 10, 5, 20),
]
MARATHON_CASES = [
    ("beginner", 20, 8, 4, 16), ("beginner", 25, 10, 5, 16), ("beginner", 30, 10, 5, 18),
    ("intermediate", 25, 10, 5, 16), ("intermediate", 30, 12, 5, 16), ("intermediate", 35, 13, 6, 16),
    ("intermediate", 40, 14, 6, 18), ("advanced", 40, 14, 5, 16), ("advanced", 45, 16, 6, 16),
    ("advanced", 50, 16, 6, 18), ("advanced", 55, 18, 6, 18), ("advanced", 60, 18, 6, 18),
    ("intermediate", 30, 12, 5, 12), ("intermediate", 35, 12, 5, 24),  # portal range edges
]
HM_PREFS = {"long_run_day": "Sat", "quality_day": "Tue", "unavailable_days": [], "preferred_rest_days": ["Sun"]}
MARATHON_PREFS = {"long_run_day": "Sat", "speed_day": "Tue", "unavailable_days": [], "preferred_rest_days": ["Sun"]}


def build_hm():
    from half_marathon_engine_main_4plus_v5_7 import build_plan

    out = {}
    for exp, cm, lr, rpw, wk in HM_CASES:
        peak, plan = build_plan(exp, cm, lr, rpw, wk, copy.deepcopy(HM_PREFS))
        out[f"{exp}-{cm}mpw-lr{lr}-{rpw}d-{wk}wk"] = {"peak": peak, "plan": plan}
    return out


def build_marathon():
    from engineV3 import build_plan

    out = {}
    for exp, cm, lr, rpw, wk in MARATHON_CASES:
        out[f"{exp}-{cm}mpw-lr{lr}-{rpw}d-{wk}wk"] = build_plan(exp, cm, lr, rpw, wk, copy.deepcopy(MARATHON_PREFS))
    return out


BUILDERS = {"hm": build_hm, "marathon": build_marathon}


def dump(data):
    return json.dumps(data, indent=1, sort_keys=True) + "\n"


def path(name):
    return GOLDEN_DIR / f"{name}.json"
