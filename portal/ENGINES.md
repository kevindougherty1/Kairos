# Kairos Engines: What the Portal Integrates

Inspection of the two running-plan engines before the portal wraps them (brief §4: "inspect the generator's
actual inputs, outputs, dependencies, and side effects"). Written 2026-11-21 from the source and from running it,
not from memory or the brief.

| Engine | File | Last commit | SHA-256 (first 12) |
|---|---|---|---|
| Marathon | `engineV3.py` (906 lines) | `5bd4df5` 2026-08-01 | `1f336ae19036` |
| Half marathon | `half_marathon_engine_main_4plus_v5_7.py` (1,347 lines) | `5bd4df5` 2026-08-01 | `9ffcf6912cf4` |

`engine.py` and `engineV2.py` are older marathon versions. Nothing imports them. The portal ignores them.

---

## Regression Baseline (2026-11-21, Python 3.14.6, `.venv`)

| Check | Result |
|---|---|
| `test_engine.py` (HM, 14 cases × 10 invariants) | **140/140 passed**, exit 0 |
| `marathon_audit.py` (12 cases) | 5 cases clean; 7 flag only **"Quality dominates week"**, the documented M-5 audit false positive (`KAIROS_CONTEXT.md`). No real issues. |
| `portal/scripts/probe_engines.py` (this doc's numbers) | 1,638 plans generated, 0 exceptions in the normal input matrix |

The marathon engine has **no assertion tests**. `marathon_audit.py` always exits 0. See "Before the adapter" below.

Re-run all three from the repo root:
```
.venv\Scripts\python.exe test_engine.py
.venv\Scripts\python.exe marathon_audit.py
.venv\Scripts\python.exe -B portal/scripts/probe_engines.py
```

---

## Shared Properties

- **Pure Python, standard library only** (`math`). `engineV3.py` also does `import random` but never uses it.
  No Flask, no third-party packages.
- **No side effects.** No file, network, database, env-var or global-state access. `build_plan()` does not mutate
  the `preferences` dict passed in (verified). Only the `print_plan()` helpers and `__main__` blocks print.
  `test_engine.py` writes `engine_tests.txt` (gitignored); the engines themselves never do.
- **Deterministic.** Same inputs give byte-identical output, within a process and across processes. There is no
  randomness or clock. Workout "styles" rotate by week number, not at random.
- **JSON-safe output.** Only dicts, lists, strings and ints, so it can go straight into a `JSONField` input/output snapshot.
- **Fast.** A full plan takes well under a millisecond. Each test script, interpreter start included, runs in about 0.1 s.
  Generation can run synchronously inside the request. No background job is needed.
- **Units: whole miles (ints).** No paces, no times, no kilometres. `current_mileage` accepts floats without error,
  but the curve rounds them.
- **No dates.** Output is week numbers (1…N) and weekday names `Mon`…`Sun`. The calendar mapping belongs to the portal (see below).
- **The race sits on `long_run_day`** of the final week. Race-week `mileage` is **6** (two 3-mile shakeouts). The race
  distance itself is not counted.

---

## Marathon: `engineV3.build_plan`

```python
build_plan(experience, current_mileage, longest_run, runs_per_week, weeks, preferences) -> list[week]
```

### Inputs

| Arg | Type | Validation in the engine | Failure |
|---|---|---|---|
| `experience` | `"beginner"` / `"intermediate"` / `"advanced"` | **none**, case-sensitive | `KeyError: 'Beginner'` |
| `current_mileage` | int, mpw | none (0 and 150 both run) | — |
| `longest_run` | int, miles | none; only a soft floor (70%) on the week-1 long run | — |
| `runs_per_week` | int 4–6 | yes | `ValueError` (friendly message) for <4 or >6 |
| `weeks` | int | **none** | `weeks ≤ 3` → `ValueError: max() iterable argument is empty`; `weeks = 4` runs but has no Base or Build phase |
| `preferences` | dict, **required** | none | missing `long_run_day` or `speed_day` → `KeyError`; `None` or `"Saturday"` → `ValueError: list.index` |

`preferences` keys: `long_run_day`, `speed_day` (required, `"Mon"`…`"Sun"`), `unavailable_days`, `preferred_rest_days`
(optional lists).

### Output

A list with one dict per week:
```python
{"week": 1, "phase": "Base", "mileage": 28,
 "sessions": {"z2_runs": [6, 5], "tempo": 4, "vo2": 4, "lr": 10, "mlr": 0},
 "schedule": {"Mon": "Z2 (6)", "Tue": "VO2 (4)", ..., "Sat": "Long Run (10)", "Sun": "Rest"},
 "warnings": []}
```
- **Phases:** `Base`, `Build`, `Peak`, `Taper`, `Race`.
- **Schedule values are display strings**, not data. All the labels it can produce: `Long Run (n)`, `MLR (n)`, `Tempo (n)`,
  `VO2 (n)`, `Z2 (n)`, `Shakeout (n)`, `Race`, `Rest`. The adapter parses them with `^(.+?) \((\d+)\)$`.
- **The peak is not returned.** `max(week["mileage"])` gives it.
- **No styles or descriptions** for workouts (the HM engine has these).

---

## Half Marathon: `half_marathon_engine_main_4plus_v5_7.build_plan`

```python
build_plan(experience, current_mileage, recent_longest_run, runs_per_week, weeks, preferences=None) -> (peak, list[week])
```

### Inputs

| Arg | Type | Validation in the engine | Failure |
|---|---|---|---|
| `experience` | same three strings | **yes** | `ValueError` |
| `current_mileage` | int, mpw | none | — |
| `recent_longest_run` | int, miles | none (soft floor, as in the marathon engine) | — |
| `runs_per_week` | int 4–6 | yes | `ValueError` |
| `weeks` | int | **none** | never raises, but `weeks ≤ 3` gives nonsense (1 week = a single Taper week); 4 = no Base or Build |
| `preferences` | dict or `None` | defaults: Sat long run, Tue quality, Sun rest | — |

`preferences` keys: `long_run_day`, **`quality_day`** (falls back to `speed_day`), `unavailable_days`, `preferred_rest_days`.
Every key is optional and defaulted.

### Output

A tuple `(peak, plan)`. Each week:
```python
{"week": 1, "phase": "Base", "mileage": 27, "peak_mileage": 42,
 "sessions": {"primary": {...}, "secondary": {...}, "lr": 8, "lr_style": "Easy LR", "z2_runs": [6, 6]},
 "primary": {"category": "Threshold Session", "miles": 4, "suggested_style": "Cruise Intervals"},
 "secondary": {...}, "lr": 8, "lr_style": "Easy LR", "z2_runs": [6, 6],      # duplicates of sessions.*
 "schedule": {"Mon": {"name": "Easy", "miles": 6, "style": None}, ...},
 "warnings": [...], "plan_warnings": [...]}
```
- **Phases:** `Base`, `Build`, **`Specific`**, `Taper`, `Race`. The marathon engine calls its third phase `Peak`.
- **Schedule values are dicts** `{name, miles, style}`. Names: `Long Run`, `Threshold Session`, `HMP Session`, `Hill Strength`,
  `Speed Support`, `Economy Support`, `Easy`, `Shakeout`, `Half Marathon Race`, `Rest`.
- Top-level `primary`/`secondary`/`lr`/`z2_runs` are **the same objects** as those in `sessions`. `plan_warnings` is
  **one list shared by every week**. The adapter must deep-copy before editing anything.
- `WORKOUT_GLOSSARY` (module constant) has a purpose, an effort cue and example sessions for every category and style.
  It's ready-made copy for the client's workout detail page.

---

## Warnings Both Engines Emit

The engines never raise on preference conflicts. They place what they can and add a warning:

| Warning | Engine | Meaning for the portal |
|---|---|---|
| `Long run day X is unavailable.` | both | **The long run is dropped from the week.** The coach must see this. |
| `Speed day conflicts with long run day.` / `Primary quality day …` | both | That quality session is dropped |
| `Not all Z2 runs could be placed.` / `Not all easy runs …` | both | Runs dropped. The week is now short of its mileage. |
| `Preferred rest day X was used for a run.` | both | Informational |
| `Could not place tempo / MLR / secondary …` | both | That session is dropped |
| `Weekly shape is chunky …` | HM | Coaching note. Common: 1,038 of 11,466 weeks in the matrix. |
| `Math check: planned mileage is N, target is N.` | HM | Schedule total ≠ stated weekly mileage |
| `plan_warnings`: current mileage above typical HM peak | HM | Plan-level note for the coach |

---

## Findings That Affect the Portal

1. **The marathon schedule can sum to more than its stated `mileage`, with no warning.** In the 819-plan
   matrix, 369 of 14,742 weeks are over (never under). All 369 come from the 3-mile easy-run floor
   (`engineV3.py:596`, applied after the week's miles are split). Most cases are unrealistic low volumes
   (10–15 mpw: 306 of them). The other 63 (≥20 mpw) are all 6-day plans: 41 beginner, 14 intermediate, 8 advanced.
   Six days leaves the most easy runs to hit the floor. The HM engine has the same kind of case (30 weeks) but
   flags it with "Math check". **Adapter default (until `TBD.md` #2 is decided):** treat the sum of the scheduled
   workouts as the truth, and add the same "Math check" warning for marathon weeks. Don't change the engine without
   tests first (brief §4.7).
2. **Neither engine validates `weeks`.** The marathon engine crashes at ≤3. Both give degenerate plans at 4.
   **Decided:** the portal enforces HM 8–20 and marathon 12–24 weeks (see Decisions).
3. **The marathon engine doesn't validate `experience` or day names.** Bad values crash with `KeyError`/`ValueError`. The portal form
   uses fixed choices (`Mon`…`Sun`, the three tiers), and the adapter validates again before calling the engine.
4. **The two engines have different contracts.** The names differ (`longest_run` vs `recent_longest_run`, `speed_day` vs `quality_day`), the return
   shapes differ (`list` vs `(peak, list)`), the schedule values differ (strings vs dicts), and the phase names differ (`Peak` vs `Specific`).
   One adapter per engine normalizes them into a single portal shape (below).
5. **A dropped long run or quality session only shows up as a warning.** The draft-review screen must show week
   warnings prominently, so a coach can't publish a plan with a missing long run without noticing.
6. **The engine puts the race on the long-run day.** **Decided:** the portal places it on the client's real race date instead (see Decisions).
7. **Existing Flask bug (not portal scope):** `app.py`'s marathon branch passes `data.get("long_run_day")`, which
   can be `None` and causes a 500. The current form always sends the field, so this doesn't trigger in practice.

---

## Adapter (built 2026-11-25 for the half marathon; marathon next)

**Status:** `portal/training/engines.py` (`PlanRequest` → `generate_half_marathon`) and `training/services.py`
(`generate_draft`, one transaction) are built and tested. The coach uses **Clients → Generate Draft**. The marathon
needs its own `generate_marathon` (same shape; add the "Math check" warning from finding 1) and a
`GENERATORS` entry. The plan below is the design it follows.

- **Location:** the engines stay at the repo root, unchanged, because Flask `app.py` still imports them. The portal adapter
  (e.g. `portal/plans/engines.py`) imports them with the repo root on `sys.path`. The Django skeleton decides how.
- **Normalized output:** one shape for both engines:
  `weeks[] = {number, phase, phase_label, target_miles, workouts[] = {weekday, kind, miles, style, title}, warnings[]}`.
  `kind` is a portal enum (`long_run`, `easy`, `tempo`, `threshold`, `vo2`, `mlr`, `hmp`, `hills`, `speed`, `economy`,
  `shakeout`, `race`). Rest days are simply missing from the list.
- **Display names (decided 2026-11-25):** `HM_WORKOUTS` maps each engine name → (kind, client title, coach label).
  Clients see "Speed Session" / "Easy Run + Strides"; the engine's pick (`engine_detail`) and glossary text
  (`suggestion`) are coach-only; the coach writes `prescription`.
- **Calendar:** anchored on the client's real race date. Race week = the Monday–Sunday week that contains the race date.
  Plan start = Monday of race week − (weeks − 1) × 7 days. Each workout date = week start + weekday index.
- **Race week:** the engine's `Race` entry moves to the actual race date. The rest of the week is left as the engine
  wrote it. The week total = shakeouts + race distance (13.1 or 26.2), so distances need decimals in the portal's
  internal unit (the engine itself only uses whole miles).
- **Input validation (before calling the engine):** experience ∈ the three tiers; runs/week 4–6; weeks HM 8–20,
  marathon 12–24; day names `Mon`…`Sun` only.
- **Versioning:** neither engine has a version constant (only the filename, and engineV3 prints "MARATHON PLAN V2").
  Store `generator_version = "<engine>@<file sha256[:12]>"` plus the git commit when one is available. Store the
  `input_snapshot` as the exact kwargs passed in.
- **Atomic save:** generate in memory (pure and fast), validate, then write the TrainingPlan and all ScheduledWorkouts in
  one `transaction.atomic()`.

### Before the Adapter (brief §4.7: regression tests before changing structure)
- ✅ **Done 2026-11-25:** `training/golden/{hm,marathon}.json` + `GoldenSnapshotTests` (16 HM + 14 marathon cases,
  incl. the 8/20 and 12/24-week edges). Refresh after an intended engine change: `manage.py engine_golden --update`.
- Add **golden-output snapshot tests** for both engines: a fixed input matrix with the JSON output committed, so any
  engine change shows up as a diff.
- Add **real marathon assertions**, mirroring `test_engine.py`'s invariants, with the M-5 check recalibrated.

---

## Decisions (Kevin, 2026-11-21)

1. **Plan length:** half marathon **8–20 weeks**, marathon **12–24 weeks**. The portal form and the adapter both enforce it.
   (The whole range ran without errors in the probe.)
2. **Race date:** Kevin works out which race the client is doing, and the coach enters it on the client (race name, date,
   distance). The plan is built backward from that date, and the race lands on the real race date.
3. **Race-week total includes the race:** shakeouts + 13.1 (HM) or 26.2 (marathon).

Still open (client-facing names, the marathon over-count): see `TBD.md` at the repo root.
