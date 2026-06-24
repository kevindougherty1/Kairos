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
├── engineV3.py                                 # ★ ACTIVE marathon engine (35-70 mi peak)
├── half_marathon_engine_main_4plus_v5_7.py     # ★ ACTIVE half marathon engine
├── test_engine.py                              # HM assertion-based test suite (14 cases × 10 invariants)
├── marathon_audit.py                           # Marathon engine diagnostic — generates plans + checks invariants
├── engine_tests.txt                            # Generated HM plan output for visual review (gitignored)
├── v5_7_fixes_summary.txt                      # Summary of v5.7 development bug fixes
├── validation_results_2026-05-17.txt           # Older validation run with red flags and analysis
├── templates/index.html                        # Frontend — race-type toggle, marathon + HM rendering
├── static/images/kpg-logo.png.PNG
└── .gitignore
```

**Active engines:** `half_marathon_engine_main_4plus_v5_7.py` (HM) and `engineV3.py` (marathon). The rest are old/archived.

---

## Half Marathon Engine Architecture

### Inputs to `build_plan()`
| Parameter | Type | Description |
|---|---|---|
| `experience` | str | `"beginner"`, `"intermediate"`, `"advanced"` |
| `current_mileage` | int | Runner's current weekly mileage |
| `recent_longest_run` | int | Recent longest run (Week 1 ceiling) |
| `runs_per_week` | int | 4–6 (7-day plans rejected, see Q-1 below) |
| `weeks` | int | Plan length (typically 12) |
| `preferences` | dict | Optional: `long_run_day`, `quality_day`, `unavailable_days`, `preferred_rest_days` |

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
- **`preferences` parameter** in `build_plan()` — `long_run_day` (default Sat), `quality_day` (default Tue), `unavailable_days`, `preferred_rest_days`
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

## Where We Left Off (2026-06-23)

M-7 implemented and verified. Marathon peak is now frequency-aware (see M-7 section below for the table). All known structural issues from the original audit are resolved.

**State now:**
- HM all 140 tests pass
- Marathon audit clean except: M-5 false positives (documented), M-8 (new minor aesthetic issue — Base LR stagnation at the 16-mi cap)
- All work committed except this M-7 batch which needs to be committed next

**Session log (cumulative across both work days):**

*2026-06-19:*
1. `c43bf49` — Cap weekly mileage jumps at +10%/+4mi; smooth climb to peak (HM Wk 9 + marathon M-1)
2. `4a59208` — Treat current_mileage and recent_long_run as guardrails, not drivers (M-6)
3. `75499c8` — Remove cutback from marathon Base phase (M-2)
4. `c5a7327` — Fix marathon Peak LR stagnation and early termination (M-4)
5. `081d2b9` — Nuke 7-day plans, cap advanced Base LR at 16, drop hard_day_style

*2026-06-23:*
6. `22804d3` — Marathon peak is now frequency-aware (M-7)
7. `eccfb8e` — Vary advanced Base LR downward at cap (M-8)
8. `bc721ff` — Fix Taper LR lift + mileage leak (M-9)
9. *(pending commit)* — Add 40% LR-to-weekly cap (M-10)

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

**~~M-3. Wk 1 LR can exceed `recent_long_run`~~** — RESOLVED 2026-06-19 via M-6 Part 1. The `max(recent, target)` pattern was replaced by `target` with `recent * 0.70` as a soft regression floor in both engines.

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

**~~M-7. Marathon peak determination is not frequency-aware~~** — FIXED 2026-06-23.

Added `PEAK_TABLE` and `frequency_peak_range()` to `engineV3.py`, plumbed `runs_per_week` into `determine_peak_mileage()`. Peak is now clamped by both tier AND frequency:

| | 4-day | 5-day | 6-day |
|---|---|---|---|
| Beginner | 32 | 38 | 45 |
| Intermediate | 42 | 50 | 55 |
| Advanced | 52 | 60 | 70 |

Lower bound is 70% of upper (a 4-day beginner doesn't drop below 22 mpw peak).

**Canonical case (adv 40/5d) resolution:**

| Wk | Before M-7 (peak 70) | After M-7 (peak 60) |
|---|---|---|
| 5 (Base end) | 57 mi, LR 16, Easy `[15, 14]` | 49 mi, LR 16, Easy `[11, 11]` |
| 9 (Build) | 64 mi, LR 20, Easy `[16, 15]` | 55 mi, LR 18, Easy `[13, 12]` |
| 13 (Peak) | 70 mi, LR 20, Easy `[14, 14, 14]` | 60 mi, LR 20, Easy `[11, 11, 11]` |

Other affected cases: most beginner peaks dropped (was 45 → now 32-38), int 5d dropped 55 → 50.

**Side effect surfaced (M-8 below):** For advanced runners at high volume, Base LR now stagnates at the cap (4-5 consecutive 16-mi LRs) because the stagnation +2 bump gets clipped back by the 16-mi advanced Base cap from Q-2.

**~~M-9. Taper distribution bugs (LR lift + mileage leak)~~** — FIXED 2026-06-23.

Surfaced during random-input diagnostic (beginner 18/4d/14wk marathon). Two related issues in `distribute_runs()`:

1. **Taper LR > Peak LR.** The "ensure LR is biggest run" rule lifted Taper LR to dominate easy runs. Random plan: peak LR was 12-13, Wk 12 Taper LR ended up as 15. Taper LRs should be intentionally smaller than peak; lifting them violates the canonical Taper principle.

2. **Systemic mileage leak from the 6-mi Taper z2 cap.** Every Taper week's schedule sum fell short of reported mileage. Adv 60/6d Wk 16: reported 52 mi, schedule summed to 36 (16-mi leak). Wk 17: 38 vs 32 (6-mi leak). The cap was incompatible with the mileage targets — the math just doesn't fit when easy runs are clamped to ≤6 mi.

**Fixes:**
- `if z2_runs and phase != "Taper":` around the LR-lift block — Taper LR stays at its calculated taper value
- Removed the `z2_runs = [min(r, 6) for r in z2_runs]` cap entirely. Easy runs in Taper can now be 8-12 mi at high volume, which preserves mileage consistency. The Taper mileage target itself already encodes the recovery — capping individual runs on top was redundant and broken.

**Results:**
| Case | Wk | Before | After |
|---|---|---|---|
| bgn 18/4d random | Wk 12 | mi=24, lr=15, z2=[6] (sched 23) | mi=24, lr=8, z2=[14] (sched 24) |
| adv 60/6d | Wk 16 | mi=52, lr=14, z2=[6,6,6] (sched 36) | mi=52, lr=14, z2=[12,11,11] (sched 52) |
| adv 60/6d | Wk 17 | mi=38, lr=10, z2=[6,6,6] (sched 32) | mi=38, lr=10, z2=[8,8,8] (sched 38) |

**Side note:** Low-frequency Taper (4-day, 14-mi z2 day) produces noticeably long "easy" runs. That's structural — at 3 runs with LR+VO2, the leftover mileage has to land on the one remaining easy day. Could revisit by keeping all runs in Taper at 4-day frequency, but deferred for now.

**~~M-10. LR-to-weekly-mileage ratio too high at low volume~~** — FIXED 2026-06-23.

Random-input diagnostic surfaced this: bgn 18/4d/14wk plan had Wk 2 LR=10 on mi=21 (48%), Wk 3 LR=11 on mi=24 (46%), etc. Coaching standard is 30-35% with up to 40% acceptable; >40% overweights weekly stress and increases injury risk.

**Fix in two places:**
1. `calculate_long_runs()` — added `lr = min(lr, int(mileage * 0.40))` after the existing Base cap. Catches the bulk of the issue.
2. `distribute_runs()` — bounded the "ensure LR is biggest run" lift at the 40% cap too. Without this, the lift was pushing LR back above the cap (Wk 5 mi=27: calculated lr=8 was lifted to 13 to dominate the leftover easy day).

**Results on bgn 18/4d random plan:**

| Wk | Before | After |
|---|---|---|
| 2 | lr=10/21 (48%) | lr=8/21 (38%) |
| 3 | lr=11/24 (46%) | lr=9/24 (38%) |
| 5 | lr=11/27 (48% after distribute lift) | lr=10/27 (37%) |
| 7 | lr=13/29 (45% after distribute lift) | lr=11/29 (38%) |

All weeks now 32-40%. Wk 10 hits exactly 40% (the cap is allowed to be 40%, not 39%).

**Structural side effect at low volume:** some weeks have an easy run tied with or larger than the LR (Wk 1: lr=7, z2=[7]; Wk 5: lr=10, z2=[10]). The "long run" label loses some weight at low volume — but the training stimulus (continuous endurance) is still distinct from easy runs (recovery), and honoring the 40% safety guideline matters more than the labeling. At higher volume the LR is naturally biggest.

**Cap doesn't bite at higher volume.** Adv 40/5d: all weeks 26-36%, well under 40%. The cap is a low-volume safety net.

**Priority order remaining:** ~~M-1~~ ✓, ~~M-2~~ ✓, ~~M-3~~ ✓, ~~M-4~~ ✓, ~~M-6~~ ✓, ~~M-7~~ ✓, ~~M-8~~ ✓, ~~M-9~~ ✓, ~~M-10~~ ✓. **No open marathon-engine bugs.** M-5 is an audit-script false positive — documented, not fixed.

**~~M-8. Advanced Base LR stagnates at 16-mi cap~~** — FIXED 2026-06-23.

When `lr == prev_lr == 16` for advanced Base (the cap), vary downward to 14 instead of letting the pre-rounding `+2` bump get clipped back. Implemented as a post-cap check in `calculate_long_runs()`.

Effect on advanced Base LRs:

| Case | Before M-8 | After M-8 |
|---|---|---|
| adv 45/6d | `12 14 16 16 16` | `12 14 16 14 16` |
| adv 50/6d | `14 16 16 16 16` | `14 16 14 16 14` |
| adv 55/6d | `16 16 16 16 16` | `16 14 16 14 16` |
| adv 60/6d | `16 14 16 16 16` | `16 14 16 14 16` |

Audit ISSUES now clear for all advanced cases. Build/Peak phases unaffected.

---

## Resolved Philosophical Questions

**~~Q-1. 7-day plans~~** — REMOVED 2026-06-19. Both engines now raise ValueError on `runs_per_week=7`. Frontend dropdown no longer offers 7. Reasoning: running 7 days/week for 14+ weeks without a rest day isn't healthy for Kairos's audience (recreational runners, not pros with coaches). The HM engine already blocked 7-day beginners; we extended the block to all 7-day plans.

**~~Q-2. Advanced Base LR ceiling~~** — CAPPED at 16 mi for advanced Base, 2026-06-19. Rationale: Pfitzinger (gold standard for serious amateurs) keeps endurance-phase LRs at 13-16 mi; Higdon Advanced doesn't hit 18 until late-plan; Hanson caps at 16 for the entire plan. Kairos's "advanced" tier is the upper end of recreational, not pros — an unsupervised online generator handing out 18-mi Base LRs is borrowing from elite programs without the coaching oversight. Build/Peak still climb to 18-20 normally. Implementation: `if phase == "Base" and experience == "advanced": lr = min(lr, 16)` in `calculate_long_runs()`.

---

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
- 7-day plans (rejected by both engines as of 2026-06-19)
- Per-runner pace targets (we're effort-first)
- Every test case producing a 100% clean shape

**Next likely tasks (ordered):**
1. **Frontend polish for marathon** — currently the marathon UI rendering may not have full parity with HM (workout glossary, plan-level notes, schedule formatting). Audit and align.
2. **Strength-training placeholder hook** — per the run+strength wedge in [[project-kairos-vision]], we need at minimum a stub UI/data structure. Doesn't have to be a full strength engine for MVP, just acknowledgement that the feature is coming.
3. **Audit script cleanup** — recalibrate the "Quality dominates week" check (M-5) so it stops producing false positives on low-mileage marathon weeks. Either remove the check, or lower the threshold to 75%+.
4. **Coach review pass** — once the engines are stable, get a human coach (or detailed self-review) to look at 4-6 representative plans end-to-end. Catches the qualitative stuff automated audits miss.

**Audience reminder (decision filter):** Kairos's target is the **recreational advanced runner buying an online plan** — not pros chasing sub-2:30. When in doubt, choose the more conservative, coach-defensible option (see Q-2 reasoning for Base LR cap as the canonical example).
