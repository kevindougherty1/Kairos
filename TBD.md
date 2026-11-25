# TBD: Parked Items

Things that need a decision or deeper work but **aren't blocking this weekend's plan**. They're parked here so
we stay on task. Each one has a safe default, so nothing waits on it. When we pick one up, move the outcome into
`PORTAL_SESSION_LOG.md` (Decisions) or the relevant doc, and delete it here.

---

## Needs Kevin's Input

### 2. Marathon weekly total can be off by a mile or two
Each marathon week has a target mileage, but the runs the engine schedules can add up to slightly **more**
(never less). Example: a beginner on 20 mpw and 6 days a week gets a week-1 target of **22 mi**, but the runs add up to **23**
(Z2 3 + VO2 3 + Z2 3 + Z2 3 + Tempo 3 + Long Run 8). Cause: easy runs have a 3-mile minimum, applied after
the week's miles are split, so a 2-mile easy run gets bumped to 3 (`engineV3.py:596`). It shows up in 369 of the
14,742 weeks tested, mostly at 10–15 mpw (unrealistic for a marathon), otherwise only in 6-day plans. The half
marathon engine has the same thing but warns about it; the marathon engine doesn't.
- **Default for now:** the portal shows the real sum of the runs and adds a "math check" warning on that week,
  so the coach sees it at review. The engine isn't touched.
- **Open:** fix it in the engine later (needs marathon regression tests first), or leave it as warning-only?

### 3. Self-serve app vs coach-led portal
`KAIROS_CONTEXT.md`'s "Roadmap to Sell" describes a self-serve app competing with Runna. The portal brief is coach-led 1:1.
They can coexist, but at some point decide whether the portal is the product or a side channel.

### 4. Strength in the portal (Phase 4)
The strength engine was retired 2026-08-01 (recoverable at `5bd4df5`). Lifting ships as `templates/strength_guide.html`.
For coaching, strength could come back as coach-written workouts rather than generated ones.

### 5. Rules for the 4 new plan types
Speed, Base/Economy, Post-race recovery and Maintenance each need a rules design session with Kevin before any
code. Speed is the best first candidate. The portal treats plan type as a generic field, so nothing waits on this.

---

## Engine Follow-Ups (don't touch this weekend)
- **Smarter workout suggestions.** The HM engine picks the workout *type* by phase (real logic), but the *style* by a
  plain week-number rotation, the same for every runner (lines 818/826/858). Its example sessions aren't sized to the
  day's miles, and in short Specific phases some HMP styles never appear. Kevin prescribes speed sessions himself
  (2026-11-25), so the suggestions are coach-only; improving them is an engine change.
- **Marathon beginner gets VO2 work every week**, including Base week 1. Classic novice programs prescribe none.
  This is a coaching-philosophy question, already logged in `KAIROS_CONTEXT.md`.
- **`marathon_audit.py` M-5 false positive:** recalibrate or drop the "Quality dominates week" check.
- **Dead code:** `engine.py` and `engineV2.py` (unused); `import random`, `build_curve`, `MIN_PEAK`/`MAX_PEAK` in
  `engineV3.py`; the 7-day rows in the HM tables. Cleanup only, so there's no behaviour change.
- **Flask `app.py` bug:** the marathon branch crashes (500) if `long_run_day`/`speed_day` are missing. The current form
  always sends them.

---

## Phase 2 Backlog (not on the weekend lists)
- **Strength workouts in the portal** (needed before selling strength/hypertrophy coaching): the coach can only edit
  generated running workouts today. Needs "add a workout" (strength sessions with exercises, sets, reps) on a plan, and
  coach-built plans with no generator. Moves TBD #4 forward.
- **How clients pay:** invoices are fine for 2–3 clients; a Stripe/Square payment link or subscription later (Phase 3+).
- **Marathon plan generation.** Add `generate_marathon` to `portal/training/engines.py` (same shape as the half marathon; add
  the "math check" warning from #2 above) and enable it in the Generate Draft form. Snapshot tests already cover the engine.
- **Phase 2 done-check walkthrough** (brief): generate → edit → publish to one client → client logs → coach reviews; drafts
  hidden; no duplicate results; regenerating keeps old plans and results. Most pieces are tested; this is the formal pass.

## Later Phases (not this weekend)
Deployment/hosting choice, HTTPS, backups, the `/api/v1/` API surface, weekly check-ins, notifications, the 4 new
block engines, and strength workflows.

## Housekeeping
- Self-host the Rethink Sans font before launch (privacy/speed); it loads from Google Fonts now.
- **Hard Left brand, before launch:** a proper trademark search (USPTO) and a domain; a real logo to replace the
  placeholder `dots` mark. The name also reads as far-left politics to some people (flagged 2026-11-25, Kevin went ahead).
- Optional: rotate the 21st API key (it was pasted in chat on day 1) at 21st.dev/mcp.
