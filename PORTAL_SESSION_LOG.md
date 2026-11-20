# Kairos Client Portal — Session Log

Running context file for the portal build session (started 2026-11-19).
I update it after every prompt so we don't lose context. The source brief is
`Kairos_Client_Portal_Implementation_Plan.md`; long-lived engine history is in `KAIROS_CONTEXT.md`.

---

## Brief summary (ingested 2026-11-19)

**Goal:** a custom client portal for a 1:1 running + strength coaching business (one coach, Kevin,
about 2–3 clients to start). Wix stays the public site and links out to the portal ("Client Login").
Kevin generates, reviews, edits and publishes plans. Clients view their workouts and log results.
Generated plans are drafts until Kevin publishes them.

**Proposed stack:** one Django app + PostgreSQL. Django templates with a little JS, and DRF for a small
`/api/v1/` surface. Session auth + CSRF. Django admin first, then a coach dashboard. The generator sits
behind an application service, not inside views. Containerized dev, pinned deps, env-var config, CI.
Managed Postgres in production, host not chosen yet. No Kubernetes.

**Generator integration rules:** inspect the real inputs, outputs and side effects first. Keep the
existing training rules. Add an adapter from validated inputs to structured plan data. Store the
generator version and an input snapshot with each plan. Save drafts atomically. Never overwrite old
plans or results. Write regression tests before restructuring. No invented training logic, and
fixtures must be labeled as fixtures.

**Models:** User (role), ClientProfile (coach FK, goals, background, prefs, timezone, units),
TrainingPlan (draft/published/archived, generator_version, input_snapshot), ScheduledWorkout
(prescription kept separate from actuals), WorkoutResult (one per workout, upsert), and WeeklyCheckIn
(next phase). Values stored in one internal unit. Minimal audit trail of published prescription edits.

**API:** `GET me/`, `GET plans/`, `GET plans/{id}/`, `PUT workouts/{id}/result/`,
`POST clients/{id}/plans/generate/` (coach), `POST plans/{id}/publish/` (coach).
Authorization is enforced server-side on every read and write.

**Phases:**
1. Foundations: inspect the source, Django project, models, migrations, auth, dev setup. *Done when:*
   fresh checkout runs from README; a coach + 2 clients can log in; clients are isolated from each other.
2. Core loop: real generator, draft/edit/publish, client schedule, result entry. *Done when:* the full
   coach→client loop works, drafts stay hidden, no duplicate results, regeneration preserves data.
3. Pilot prep: mobile polish, API, tests, deploy config, ops docs, staging, HTTPS, password-reset email,
   backups, restore process, DEBUG off.
4. Expand from real feedback: check-ins, progress, strength workflows, notifications.

**Deliverables:** source + migrations, README, `.env.example`, synthetic demo data, tests, API docs,
production-readiness notes, and a progress summary (done / mocked / missing / remaining).

---

## Reconciliation with the current repo (things the brief didn't know)

1. **Generator source is present.** The brief says `engineV3.py` was "not inspected". It's in this
   repo, along with the HM engine `half_marathon_engine_main_4plus_v5_7.py`. Both are active, both
   expose `build_plan()`-style entry points, and both are pure stdlib. HM has `test_engine.py`
   (140 assertions) and marathon has `marathon_audit.py`.
2. **Flask vs Django.** The current app is Flask (`app.py`, the only dep), and the KAIROS_CONTEXT
   roadmap says "Flask stays". The brief proposes Django. Undecided: should the portal be a new Django
   project that imports the engines, or should the Flask app be extended?
3. **Business model shift.** KAIROS_CONTEXT's "Roadmap to Sell" describes a self-serve SaaS that
   competes with Runna. The brief describes a coach-led 1:1 portal. These may coexist; the decision is open.
4. **Strength.** The brief lists "strength programming workflows" for Phase 4. The strength engine was
   retired on 2026-08-01 (recoverable at `5bd4df5`), and lifting now ships as
   `templates/strength_guide.html`. For a coach-led portal, strength could come back as coach-authored
   workouts rather than generated ones.
5. **Uncommitted work on master.** The session-4 changes are staged: strength engine deletion, strength
   guide, `index.html`/`app.py` cleanup and context doc updates. The brief itself is untracked.
   It should be committed before portal work starts.

## Decisions (locked 2026-11-19)
- [x] **Django.** Kevin leaned toward it for the resume, and it also fits the work better: built-in
  admin, auth, password reset, ORM + migrations, and an established path for role/ownership checks.
  These are exactly what the portal needs. The existing Flask public generator (`app.py`) stays as is.
- [x] **Portal lives in `portal/`** in this repo and imports the engines as they are.
- [x] **Session-4 work committed** before portal work starts.
- [x] **v1 plan types:** Half marathon and marathon (existing engines), plus two new non-race blocks:
  a **Speed block** and a **Base / Running economy block**. The new blocks need new training logic,
  so the rules must be designed with Kevin and not invented (as the brief requires).
- [ ] Additional block types suggested to Kevin, awaiting his call: post-race recovery/reverse taper,
  and maintenance/bridge between races. See prompt 2.

## Pending
- Kevin is importing some GitLab repositories **before website design starts**. Inspect them once
  they're in.

---

## Prompt log

### 1 — 2026-11-19 — Ingest brief, start session log
- Read `Kairos_Client_Portal_Implementation_Plan.md` and `KAIROS_CONTEXT.md`, checked repo state.
- Created this file. No code changes.
- **Next:** resolve the open decisions above, then begin Phase 1 (engine I/O inspection → Django skeleton).

### 2 — 2026-11-19 — Decisions + commits
- Kevin approved: Django, `portal/` folder, commit session-4 first, v1 = HM + marathon + Speed block +
  Base/Economy block.
- HM suite 140/140 on the staged state, then committed:
  1. "Retire strength engine; ship lifting as a written guide" (session-4 work)
  2. "Add client portal brief and session log" (brief + this file)
- Suggested two more block types (recovery/reverse-taper, maintenance/bridge) and am waiting on Kevin.
- **Next:** Kevin imports GitLab repos, then I inspect them and start Phase 1.
