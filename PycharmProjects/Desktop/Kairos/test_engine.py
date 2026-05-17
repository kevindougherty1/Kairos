import io
import contextlib
from half_marathon_engine_main_4plus_v5_7 import build_plan, print_plan

tests = [
    ("beginner",      20,  8, 4, 12),
    ("beginner",      30, 10, 5, 12),

    ("intermediate",  25,  8, 5, 12),
    ("intermediate",  35, 10, 5, 12),
    ("intermediate",  40, 12, 6, 12),

    ("advanced",      40, 10, 5, 12),
    ("advanced",      45, 12, 5, 12),
    ("advanced",      55, 14, 6, 12),
]

with open("engine_tests.txt", "w") as f:
    for test in tests:
        exp, current, recent_lr, rpw, weeks = test

        peak, plan = build_plan(
            experience=exp,
            current_mileage=current,
            recent_longest_run=recent_lr,
            runs_per_week=rpw,
            weeks=weeks,
        )

        f.write(f"\n{'='*60}\n")
        f.write(f"TEST: {test}\n")
        f.write(f"{'='*60}\n")

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            print_plan(peak, plan)
        f.write(buffer.getvalue())