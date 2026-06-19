# Kairos (KPG) — Project Context

## What Is This

Kairos is a training plan generator for runners. The web app (Flask) takes runner inputs and returns a structured week-by-week training plan. Currently has a half marathon engine and a marathon engine. The half marathon engine is the active development focus.

**GitHub:** https://github.com/kevindougherty1/Kairos

---

## File Structure

```
Kairos/
├── app.py                                      # Flask entry point — imports both engines, routes on race_type
├── engine.py                                   # Marathon engine v1 (old)
├── engineV2.py                                 # Marathon engine v2 (old)
├── engineV3.py                                 # Marathon engine v3 — marathon engine app.py uses (35-70 mi peak)
├── half_marathon_engine_main_4plus_v5_7.py     # ★ ACTIVE half marathon engine
├── test_engine.py                              # Assertion-based test suite (12 cases × 10 invariants)
├── engine_tests.txt                            # Generated plan output for visual review (gitignored)
├── v5_7_fixes_summary.txt                      # Summary of v5.7 development bug fixes
├── validation_results_2026-05-17.txt           # Older validation run with red flags and analysis
├── templates/index.html                        # Frontend — race-type toggle, marathon + HM rendering
├── static/images/kpg-logo.png.PNG
└── .gitignore
```

**The active half marathon engine is `half_marathon_engine_main_4plus_v5_7.py`.** Everything else is either the marathon engine or old/archived files.

---

## Half Marathon Engine Architecture

### Inputs to `build_plan()`
| Parameter | Type | Description |
|---|---|---|
| `experience` | str | `"beginner"`, `"intermediate"`, `"advanced"` |
| `current_mileage` | int | Runner's current weekly mileage |
| `recent_longest_run` | int | Recent longest run (Week 1 ceiling) |
| `runs_per_week` | int | 4–7 (engine enforces 4+) |
| `weeks` | int | Plan length (typically 12) |
| `preferences` | dict | Optional: `long_run_day`, `quality_day`, `unavailable_days`, `preferred_rest_days`, `hard_day_style` |

### Plan Structure
Each week in the returned plan has:
- `phase` — Base / Build / Specific / Taper / Race
- `mileage` — weekly total
- `primary` — main quality workout (Threshold or HMP Session)
- `secondary` — supporting workout (Hill Strength, Speed Support, Economy Support)
- `lr` / `lr_style` — long run miles and style label
- `z2_runs` — list of easy run mileages
- `schedule` — day-by-day assignment (Mon–Sun)
- `warnings` — week-level shape issues
- `plan_warnings` — plan-level warnings (e.g., current mileage exceeds tier cap)
- `peak_mileage` — plan peak

### Phase Breakdown (12-week plan)
- **Base** × 3 weeks — aerobic base, easy LRs, threshold work
- **Build** × 4 weeks — mileage climbs, LR grows, cutback in final Build week
- **Specific** × 2 weeks — HMP sessions, peak mileage
- **Taper** × 2 weeks — mileage drops ~30% / ~48%, LR reduced
- **Race** × 1 week — 6 miles, shakeout runs placed on schedule

### Key Functions
| Function | Role |
|---|---|
| `determine_peak_mileage()` | Computes plan peak from ramp formula, clamps to frequency tier |
| `frequency_peak_range()` | Returns `(lower, upper)` peak bounds per experience × frequency |
| `weekly_curve()` | Builds weekly mileage list across all phases |
| `raw_long_runs()` | First-pass LR targets based on % of weekly mileage |
| `apply_long_run_wave_logic()` | Prevents 3 consecutive cap-LR weeks |
| `apply_taper_long_runs()` | Sets taper LRs to ~65% / ~50% of peak LR |
| `calc_lrs()` | Runs all three LR passes in order |
| `optimize_week_shape()` | Adjusts LR and primary up to make easy runs cleaner |
| `base_week_mileage_adjustment()` | Trims Base-week mileage when easy runs would dwarf LR |
| `build_week_schedule()` | Places workouts onto Mon–Sun using preferences |
| `build_plan()` | Orchestrates everything, returns `(peak, plan)` |

---

## Peak Mileage Logic

Peak is bound by three concepts (formerly conflated into a single tier table):

**1. Clean shape cap** — max weekly mileage that distributes without forcing easy runs above their soft cap. **Derived** from `lr_cap + 7 (primary) + 5 if applicable (secondary) + (n_easy × soft_cap)`. Beginner rows are hard injury-conservative caps, NOT derived from shape math.

```
4-day:  beginner 28, intermediate 39, advanced 43
5-day:  beginner 32, intermediate 42, advanced 48
6-day:  beginner 38, intermediate 47, advanced 52
7-day:  intermediate 54, advanced 60  [beginner 7d blocked]
```

**2. Experience ceiling** — `MAX_PEAK = 60` is the only hard absolute. Beginner-specific caps are baked into the table above.

**3. Tolerance extension** — when growth at clean cap < 25%, upper extends to `1.10 × clean_cap` (capped at `MAX_PEAK`). **Only fires on 4d/5d** — for 6d/7d runners, "add a day" is not realistic advice, so their frequency choice is respected and the plan stays at clean cap. Beginners never extend (injury risk).

```
intermediate 4d/5d: 1.10
advanced     4d/5d: 1.10
beginner          : 1.00 (disabled)
6d/7d (any exp)   : disabled
```

**Over-qualified runner handling**: `current_mileage` is honored as a floor only up to the runner's effective upper bound — it cannot push peak above the clean cap. A 55 mpw advanced runner on 6d peaks at 52 (clean), not 55. The plan note acknowledges the volume mismatch: *"This plan focuses on race-specific structure at a clean weekly volume; you can keep your additional easy miles outside the plan if you'd like."*

Code: `frequency_peak_range()`, `determine_peak_mileage()`, `weekly_curve()` (clamps starting volume at peak).

---

## Long Run Caps

```
beginner:      12 mi
intermediate:  14 mi
advanced:      16 mi
```

Tier-only caps — no frequency-based reductions. 16 is the absolute ceiling across any HM plan.

---

## Bugs Fixed (v5.7 development)

### Fix 1 — Wave Logic Conflict
**Problem:** `calc_lrs()` applies wave logic to reduce LR variety (e.g., 14/12/14 instead of 14/14/14). But `optimize_week_shape()` would see the reduced LR, call it "ugly", and raise it back up — undoing the wave.

**Fix:** Added `lr_ceiling` parameter to `optimize_week_shape()`. In `build_plan()`, pre-wave LRs (`raw_long_runs()`) are compared to post-wave LRs (`calc_lrs()`). Wave-reduced weeks get their reduced value as the optimizer ceiling; other weeks get the full cap.

---

### Fix 2 — Beginner 4-Day LR Stagnation
**Problem:** Beginner 4-day runners had LR stuck at 8 miles all plan, never reaching the 12-mile cap.

**Two root causes:**
1. `base_long_run_target()` used 30-32% of mileage regardless of frequency — too low for 4-day plans at low volume
2. Python banker's rounding: `round(9/2)*2 = 8` (not 10)

**Fix:** Frequency-aware target percentages for 4-day (Base 32%, Build 38%, Specific 44%) and `math.ceil` rounding instead of `round` for 4-day plans. _(The even-rounding step has since been dropped — see "Follow-up improvements" below.)_

---

### Fix 3 — Advanced 7-Day Base Phase Downward Trend
**Problem:** High-mileage runners (e.g., 50 mpw entering a 60 mpw plan) saw their base weeks declining because `normal_base_end = round(peak * 0.82)` was below their starting mileage.

**Fix:** In `weekly_curve()`, when `current_mileage >= normal_base_end`, compute a `base_end` slightly above current mileage (capped below the build entry point). Ensures base phase holds or gently rises.

---

### Fix 4 — Advanced 7-Day Peak Week Quality Load
**Problem:** Primary + secondary workouts consumed ~53% of weekly mileage at peak for advanced runners.

**Fix:** Post-optimizer quality budget cap: `25%` for advanced, `28%` for others. Excess miles from secondary returned to `z2_runs` to keep totals exact. Placed *after* `optimize_week_shape()` so the optimizer can't undo it.

---

### Fix 5 — Peak Mileage Below Current Mileage
**Problem:** Advanced 5-day runner at 45 mpw received a plan with peak = 44 mi. The plan dropped mileage in week 1 and never recovered to the runner's actual fitness.

**Fix:** One line in `determine_peak_mileage()`:
```python
peak = max(peak, min(current_mileage, MAX_PEAK))
```

---

### Fix 6 — Advanced 5-Day 16-Mile Long Runs
**Problem:** At 44-45 mpw on 5 days, easy runs landed at [11, 10] which the optimizer flagged as "ugly," causing it to raise LR from 14 → 16. This also meant wave logic never fired (raw LRs were 14, wave only checks against cap=16 which they never hit). Three consecutive 16-mile LRs appeared in Build.

**Four-part fix:**
1. `lr_cap()`: advanced 5-day capped at 14
2. `easy_run_soft_cap()`: advanced 5-day raised 9 → 10
3. `ugly_distribution()` 5-day threshold: `>= 10` → `>= 11` (two 10-mile easy days at this volume is fine)
4. `ugly_distribution()` proximity check: added `and max(z2_runs) >= 12` (prevents wave-reduced week LR=12/easy=11 from false-positive triggering)

_(Item 1 — the 5-day cap reduction — has since been removed. See "Follow-up improvements" below.)_

---

## Follow-up Improvements (May 2026)

### Long-run variety (`1cca541`)
- Dropped even-only rounding at all 5 LR rounding sites; odd LR lengths now allowed
- Removed the 5-day adv cap reduction; universal LR ceiling is 16
- Phase % bumped for 5+ day plans: Build 31 → 33, Specific 32 → 35 (restores Base→Build LR step, keeps Specific ≥ Build at peak)
- Optimizer step `lr+2` → `lr+1`; taper safety `first-2` → `first-1`

**Effect on the original flat plan (adv 40 / 5d):**
- Before: `10, 12, 12, 12, 12, 12, 12, 12, 14` (five flat 12s)
- After: `10, 12, 12, 13, 14, 14, 12, 14, 15`

### 4-day cap differentiation (`34b62f8`)
- Removed the 4-day reduction in `lr_cap()` entirely
- Caps are now pure tier (beg 12, int 14, adv 16) regardless of frequency
- Effect: adv 4d peak LR goes from 12 to 16, int 4d from 12 to 14

### Beginner quality-day reduction
- `secondary_workout()` now returns "None" for beginners regardless of frequency
- Beginners at 5+ day frequency get 1 primary + LR + extra easy day (previously 2 quality days)
- Intermediate / advanced unchanged (still 2 quality days at 5+ day)

### Peak mileage logic refactor (principled replacement of the tier table)
- Replaced the conflated `(lower, upper)` tier table with three explicit concepts: clean shape cap, experience ceiling, tolerance extension (see "Peak Mileage Logic" section above)
- Subsumed the earlier int-5d-specific patch — same logic now applies uniformly across all tiers
- Effects on previously broken tiers:
  - adv 40/5d: 44 → 48 (was +10% growth, now +20% via extension)
  - adv 45/5d: 45 → 48 (was 0% growth — pointless plan — now +7%)
  - adv 55/6d: 58 → 60 (ceiling-bound, with "consider 7d" warning)
  - adv 50/7d, 55/7d: 58 → 60 (ceiling-bound)
  - int 50/6d (new test case): 52 → 57 (extension fires correctly)
- Beginner caps unchanged (`TOLERANCE_MULT = 1.00` — injury risk takes priority over overload pressure)
- Added 3 edge-case tests: int 50/6d, adv 50/5d, adv 55/7d
- High-mileage cases fire the existing "Weekly shape is chunky" warning at peak week — informational, not a regression
- New test cases added: int 30/5d, int 40/5d (alongside existing int 25/5d, int 35/5d)

### Long-run style: Fast Finish reserved for final Specific week
- Previously `long_run_style()` returned "Fast Finish LR" for any Specific week with `lr >= cap`, producing back-to-back race-simulator LRs at peak fatigue
- Now `is_final_specific` is passed in; only the last Specific week becomes Fast Finish
- Earlier Specific weeks become Progression LR (race-pace contact without the brutal closing demand)

### Week 1 LR shape: no regression, target-driven, sanity-capped
- Old `initialize_week1_lr` capped Week 1 LR at exactly `recent_longest_run`, which produced visually weak LRs (e.g., 10-mi LR alongside [8, 7] easy days) and could regress runners below their recent ability
- New logic: `lr = max(target_lr, recent_longest_run)` sanity-capped at `target × 1.2`
- `recent_longest_run` is treated as a readiness guide, not a hard ceiling (same principle as `current_mileage`)
- `base_week_mileage_adjustment` also relaxed from -4 to -5 mi reduction cap so it can fully resolve oversized easy runs in Base wk 1
- Effect: int 35/5d wk 1 goes from LR 10 / easy [8, 7] → LR 11 / easy [7, 7] (LR now dominates by 4 mi instead of 2)

### Quality decoupled from weekly mileage (`PRIMARY_MILEAGE` / `SECONDARY_MILEAGE` tables)
- Replaced the `weekly_mileage * 0.14` and `* 0.10` percentage formulas with phase-position progression tables
- Each entry is `(phase_start, phase_peak)` — workout mileage interpolates linearly across the phase
- For Build phase with ≥ 4 weeks, peak lands at the **second-to-last** week; final week is a true cutback at 0.75 × peak (~25% reduction)
- Result: classic cutback shape (e.g., intermediate Build primary: 5, 6, 7, 5) where quality reduces meaningfully along with volume, not just volume in isolation
- Coaching-defensible absolute mileages: a coach can look at "intermediate Build peaks at 7 mi Threshold, drops to 5 on the cutback" and agree or disagree, instead of inferring intent from a percentage

### Frontend wired in (`20fdf0d`)
- `app.py` now routes `/generate-plan` on `race_type` and calls the HM engine when requested
- `index.html` adds a race-type toggle and HM-specific summary rendering (primary / secondary / LR style)

---

## V6 Product Layer (Merged In)

An earlier V6 draft contributed a product/app layer on top of the core engine. These additions live in v5.7:

- **`WORKOUT_GLOSSARY`** — purpose, effort cue, and example prescriptions for every workout type
- **Scheduling layer** — `build_week_schedule()` places workouts onto Mon–Sun based on `preferences`
- **`preferences` parameter** in `build_plan()` — `long_run_day` (default Sat), `quality_day` (default Tue), `unavailable_days`, `preferred_rest_days`, `hard_day_style`
- **Global plan warnings** — fires when `current_mileage > recommended_upper` for the runner's tier
- **`print_plan()` enhanced** — `show_styles`, `show_schedule`, `show_glossary` flags; prints day schedule and plan-level notes
- **`print_workout_glossary()`** — prints the full glossary
- **`HMP Blocks`** added to Specific phase primary rotation

---

## Test Suite

**File:** `test_engine.py`
**Output:** `engine_tests.txt` (gitignored — generated)

**Test cases (8 total):**
```python
("beginner",      20,  8, 4, 12)   # PASS  peak=28
("beginner",      30, 10, 5, 12)   # PASS  peak=32
("intermediate",  25,  8, 5, 12)   # PASS  peak=42
("intermediate",  35, 10, 5, 12)   # PASS  peak=42
("intermediate",  40, 12, 6, 12)   # WARN  peak=52  (chunky wk9 — structural)
("advanced",      40, 10, 5, 12)   # PASS  peak=44
("advanced",      45, 12, 5, 12)   # PASS  peak=45  (was RED FLAG before fix 5)
("advanced",      55, 14, 6, 12)   # WARN  peak=58  (chunky wks 5,9 — structural)
```

**Structural chunky warnings** on intermediate 40/6d (wk9) and advanced 55/6d (wks 5,9) are inherent to high mileage on 6 days — not bugs, the warning message is accurate.

Run with: `python test_engine.py`

---

## Where We Left Off (2026-06-19)

Reviewing the **intermediate / 35 mpw / 5-day / 12-week** plan against the engine's current state. All 170 assertion tests pass, but the *shape* still has hiccups the test suite doesn't catch. Working toward MVP — see below.

Plan output snapshot (int 35/5d, peak 46):

```
Wk 1  Base    32   Thr(4) Hill(3)   LR 11           Easy [7, 7]
Wk 2  Base    33   Thr(4) Speed(4)  LR 11           Easy [7, 7]
Wk 3  Base    34   Thr(5) Econ(4)   LR 11           Easy [7, 7]
Wk 4  Build   39   Thr(5) Speed(4)  LR 13           Easy [9, 8]
Wk 5  Build   41   Thr(6) Hill(4)   LR 14           Easy [9, 8]
Wk 6  Build   42   Thr(7) Speed(5)  LR 14           Easy [8, 8]
Wk 7  Build   36   Thr(5) Econ(4)   LR 12           Easy [8, 7]   ← cutback
Wk 8  Spec    40   HMP(6) Speed(4)  LR 14           Easy [8, 8]
Wk 9  Spec    46   HMP(8) Hill(5)   LR 14 FastFin   Easy [10, 9]  ← peak, chunky warn
Wk 10 Taper   32   Thr(4)           LR 9            Easy [7, 6, 6]
Wk 11 Taper   24   Thr(4)           LR 7            Easy [5, 4, 4]
Wk 12 Race    6                                     Shakeouts
```

---

## Open Problems

Living list. Add items the moment we notice them. Don't archive without resolution or explicit deferral.

### ~~Wk 9 peak jump too steep (int 35/5d)~~ — FIXED 2026-06-19
- Was: Build cutback Wk 7 = 36 → Wk 8 = 40 → Wk 9 peak = 46 (+11%, +15% jumps)
- Now: Wk 7 = 38 → Wk 8 = 42 → Wk 9 = 46 (+10.5%, +9.5% jumps)
- **Principle added:** no week-over-week increase exceeds max(+10%, +4 mi). Cutback floor is computed by stepping backward from peak through Specific phase. Specific phase switched to linear interpolation so the curve's own easing doesn't put the steepest jump on the final week.
- `segment()` gained `cutback_floor` and `exponent` params. `weekly_curve()` computes `min_cutback` from peak + `specific_n` and passes it to the Build segment.
- Chunky warning at Wk 9 still fires for int 35/5d — that's the LR/easy distribution at peak on 5d, unrelated to the cutback.
- Verified on adv 55/6d: cutback 50→44 (-12%), Spec 44→48→52, both +9.1%/+8.3%. Generalizes.

### Marathon engine audit (2026-06-19)

Ran `marathon_audit.py` across 12 tier × frequency × volume cases. Findings:

**~~M-1. Final week-to-peak jump (~+11–12%)~~** — FIXED 2026-06-19. Ported the HM cutback-floor + linear-final-segment fix to `engineV3.py`. Results:

| Case | Before | After |
|---|---|---|
| bgn 20/4d | 40 → 45 (+12.5%) | 41 → 45 (+9.8%) |
| int 25/5d | 49 → 55 (+12.2%) | 51 → 55 (+7.8%) |
| int 35/6d | 49 → 55 (+12.2%) | 51 → 55 (+7.8%) |
| adv 40/5d | 63 → 70 (+11.1%) | 65 → 70 (+7.7%) |
| adv 45/6d | 63 → 70 (+11.1%) | 65 → 70 (+7.7%) |

`build_segment` (nested in `generate_weekly_mileage`) gained `cutback_floor` and `exponent` params. `min_cutback` is computed from peak by stepping backward through `peak_n` weeks. Peak segment uses `exponent=1.0`.

**~~M-2. Base phase ends with a cutback~~** — FIXED 2026-06-19. Base segment now called with `cutback=False`. Base is the establishment phase — no load applied yet, nothing to recover from.

Effect on int 25/5d: Wk 1-5 `28 31 36 40 34` (trough) → `28 31 35 39 43` (clean ramp). The +10%/+4 global cap from M-6 keeps the Base ramp from getting too aggressive even with the cutback removed.

**M-3. Wk 1 LR can exceed `recent_long_run`** — `calculate_long_runs()` uses `lr = max(recent_long_run, target_lr)` for Wk 1 with no sanity cap. An adv 60/7d runner with recent LR=18 gets Wk 1 LR=20. HM engine solved this with `min(lr, target × 1.2)` in `initialize_week1_lr()`. Port the same approach.

**~~M-4. Peak LR issues~~** — FIXED 2026-06-19.

Three issues, one underlying cause: even rounding ran *after* the 20-control logic, so `lr=19` would bypass the spacing rule and become a stealth 20 via `round(19/2)*2 = 20`.

Fixes in `calculate_long_runs()`:
- Even rounding moved BEFORE the 20-control and the Base-stagnation check so they see the actual final LR
- Dropped the `twenty_count >= 2` total cap (was cutting off Peak prematurely — once Build hit 2 twenties, Peak couldn't reach 20)
- Added `is_peak_week` exemption — the highest-mileage Peak week is sacred and always gets its 20 regardless of the back-to-back spacing rule

Effects:
- adv 60/7d Base: `20 20 20 20` → `20 18 20 18` (proper spacing)
- adv 55/6d Peak: maxes at 18 → maxes at 20 on peak week
- adv 40/5d, 45/6d: Peak LR reaches 20 on the peak week
- adv 50/6d: 3-consecutive 16s in Base resolved by post-rounding stagnation check

**M-5. Audit-check false positive (not a real bug):**
- "Quality dominates week" check flags 60–76% on low-mileage weeks, but for marathon the LR alone is 30–35% of weekly volume. Adding VO2+tempo legitimately puts quality at 60%+ on a 22 mpw beginner week — and the easy run distribution still works out fine (1 easy day at 6 mi). Audit check needs recalibration or removal, not the engine. Documenting so we don't chase this later.

**~~M-6. Inputs driving structure, not guarding it~~** — FIXED 2026-06-19 (Parts 1 & 2).

**Principle established:** `current_mileage` and `recent_long_run` are GUARDRAILS (what the engine should not spit out — no regression, no overload), not DRIVERS (don't compute structure from them). Structure derives from phase logic + peak + experience; inputs constrain the output.

**Part 1 — Wk 1 LR no longer lifted by `recent_long_run`:**
- Marathon `calculate_long_runs()`: `lr = max(recent_long_run, target_lr)` → `lr = target_lr` with `regression_floor = round(recent * 0.70)` as soft floor
- HM `initialize_week1_lr()`: same change — phase logic drives, recent_lr only prevents embarrassing regression below 70%
- Effects: marathon int 25/5d Wk 1 LR 10→8, marathon adv 40/5d Wk 1 LR 14→12 (target was higher, recent inflated less so smaller change for HM)

**Part 2 — Global +10%/+4 mi week-over-week guardrail:**
- Both engines post-process the weekly curve. Any climbing week exceeding `max(+10%, +4 mi)` over prior gets capped. Cutbacks and Taper/Race weeks untouched.
- Effects: marathon int 25/5d Wk 3 jump 31→36 (+16%) → 31→35 (capped at +4); same pattern smooths all Base/Build climbs
- HM curves were already within cap (no visible changes), but the rule is in place as a guard

This subsumes M-3 (Wk 1 LR regression guard — now handled by the regression_floor pattern). M-2 (Base shouldn't cutback) is independent semantic cleanup. M-4 (Peak LR stagnation/early termination on advanced runners) remains as-is.

**Priority order remaining:** ~~M-1~~ ✓, ~~M-2~~ ✓, ~~M-3~~ ✓, ~~M-4~~ ✓, ~~M-6~~ ✓. All known marathon-engine bugs resolved as of 2026-06-19. The only flags left in the audit script are the M-5 false positives ("Quality dominates week") which we documented as audit-check miscalibration, not an engine issue.

Both engines are now in a good state for MVP consideration. Next likely work: frontend polish for marathon UI parity with HM, or a strength-training placeholder hook (per the run+strength wedge in [[project-kairos-vision]]).

---

## MVP Roadmap

**Goal:** ship a consumer-facing version of Kairos (HM + marathon plan generators) that's good enough for early users without polishing forever.

**Guiding tension:** lots of bug fixes are still ahead, but we don't want to overfit. Every fix should be expressible as a principle — not a special case for one input combo. If a fix can only be stated as "and also when experience=intermediate and frequency=5 and current_mileage in [35, 45]…", that's a signal to step back.

**What "MVP" means here (draft — refine as we go):**
- Both engines produce a coach-defensible plan for the common cases (no obvious shape bugs, sensible quality progression)
- Frontend renders both race types cleanly
- Effort-first language present in workout descriptions (per [[project-kairos-effort-philosophy]])
- Strength training has at least a placeholder hook (the run+strength combo is the strategic wedge per [[project-kairos-vision]])
- Known edge cases documented, not necessarily fixed

**What MVP does NOT require:**
- 3-day engine
- 7-day beginner support
- Per-runner pace targets (we're effort-first)
- Every test case producing a 100% clean shape

**Next likely tasks (ordered):**
1. Diagnose + fix the Wk 9 peak jump principle (not just for int 35/5d, but as a `weekly_curve()` invariant)
2. Audit the marathon engine (`engineV3.py`) the same way we audited the HM engine — generate plans, list hiccups
3. Decide what level of "good enough" each engine needs before MVP cut
4. Frontend polish pass once engines are stable
