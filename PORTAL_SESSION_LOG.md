# Kairos Client Portal: Session Log

Running context for the portal build (started 2026-11-19), updated after every prompt.
- Brief: `Kairos_Client_Portal_Implementation_Plan.md`. Decisions below override it (e.g. the brief still says Wix).
- Engine history: `KAIROS_CONTEXT.md`. Engine contract for the portal: `portal/ENGINES.md`.
- Parked items (not this weekend): `TBD.md`.

---

## ▶ START HERE (Wed 2026-11-25, catching up on Sunday's list)

**Phase 1 is signed off** (fresh checkout → README → coach + 2 clients isolated). Brand is now **Hard Left**
(display only). Sunday items left: the **public pages** (waiting on Kevin's facts). The stretch adapter is done (HM drafts).

### Resume here
1. **Start Docker Desktop**, then from `portal/`: `docker compose up -d` → `..\.venv\Scripts\python.exe manage.py runserver`.
   WSL/Docker is capped at 3 GB (`%USERPROFILE%\.wslconfig`). Stop the dev server when you're done.
2. **Kevin:** create the admin login once: `.venv\Scripts\python.exe portal\manage.py createsuperuser`.
3. **Public pages need from Kevin:** the offer (prices shown or "contact me"), location (or online-only), a 2–3 line
   bio, the inquiry email address. Photos: licensed stand-ins approved (2026-11-25).
4. Then: the public pages with taste-skill (kind = service; arm its gate in `portal/` once the page exists).
   Phase 2 next steps: marathon adapter, coach editing of draft workouts, publish (archives the old plan).

---

## Decisions

| Area | Decision |
|---|---|
| Brand name | **Hard Left** (the hard left turn of track running), **display only** (2026-11-25): site, titles, emails, admin. Code/file names stay `kairos`. Placeholder mark = taste-skill's dealt `dots` until a real logo exists. |
| Framework | **Django** portal in `portal/`, importing the HM + marathon engines unchanged. Flask `app.py` stays as is. |
| Public site | **No Wix.** Home/Offer, About, Inquiry, Client Login are Django too, and ship first. |
| Plan types (v1) | HM + Marathon (existing engines); Speed, Base/Economy, Post-race recovery (2–4 wk), Maintenance (new: rules design session with Kevin before code). `plan_type` is a generic field. Deferred: 10K, return-from-injury. |
| Copy | Title Case headings and buttons, sentence case body. |
| Dev database | **Docker Desktop + Postgres 17.12** via `portal/docker-compose.yml`. Django runs from `.venv`. |
| Stack versions | Django **6.1.3**, psycopg 3.3.9, django-environ 0.14.0, pinned in `portal/requirements.txt` (2026-11-21). |
| Plan length | HM **8–20** weeks, marathon **12–24** weeks, enforced by the form + adapter (2026-11-21). |
| Race date | Kevin works out the client's race; the coach enters race name/date/distance. The plan is built backward from the race date, and the race lands on the real date (2026-11-21). |
| Race-week total | Includes the race: shakeouts + 13.1 / 26.2, so distances need decimals (2026-11-21). |

## Toolkit (installed and verified)

| Skill / tool | Role | Source / install |
|---|---|---|
| `design-taste-frontend` | Sets the visual system (public + portal) | junction → `gitlab-imports\taste-skill` (`f6b7657`, gitignored) |
| `design-md` | 84 reference DESIGN.md systems; Kairos tokens go in `portal/DESIGN.md` | wrapper + junction `library/` → `gitlab-imports\awesome-design-md` (`fcc7028`) |
| `web-design-guidelines` | Quality gate before any page is "done" | vendored, rules pinned at `434b7f9` |
| `playwright-cli` | Headless Edge: screenshots, console/network errors, overflow | `npm i -g @playwright/cli` 0.1.25 + version-matched skill; `.playwright/cli.config.json` = msedge |
| `21st-ui` + 21st MCP | Search 21st.dev components, **rebuild as Django + CSS** (never npm/shadcn), read-only | `.mcp.json` + user env var `API_KEY_21ST`; connects via OAuth sign-in |

- **Precedence:** Kevin's decisions > taste-skill > design-md / 21st > (gate) web-design-guidelines. Logged-in app
  screens relax taste-skill's landing-page-only rules (one section per screen, hero moments).
- **"Check my work" routine for every page:** localhost → screenshots at 390 + 1280 → `console` → `requests` →
  overflow check → view screenshots → fix → web-design-guidelines review → only then show Kevin.
- **Environment:** Python 3.14.6 in `.venv`; node v26.13.1; Docker 29.9.3 / Compose v5.7.0 on WSL 2 (Ubuntu).

## Gotchas
- Use `.venv\Scripts\python.exe`. Bare `python` is the Windows Store alias.
- Run `playwright-cli` from **PowerShell** (Git Bash mangles `$APPDATA` paths). It blocks `file://`, so test via `http://localhost`.
- Delete a junction with `cmd /c rmdir`, never `Remove-Item -Recurse` (that can wipe the target).
- PowerShell 5.1 `Set-Content -Encoding utf8` adds a BOM, so strip it from files git reads.
- Connect to Postgres via **`127.0.0.1`**, not `localhost`: here `localhost` tries IPv6 `::1` first, which Docker
  doesn't listen on, and the connection stalls. Settings default to 127.0.0.1, with a 5 s connect timeout.
- If tools or env vars go missing, the terminal predates the install: fully exit PyCharm (File → Exit) or reboot.
- 21st free tier: **2 `get_component` calls a day**, so search first and retrieve once. AI generation is off.
- The taste-skill clone is shallow, so its git history is incomplete.

## Fresh-checkout setup (goes into the README in Phase 1)
Clone taste-skill + awesome-design-md into `C:\Users\kevin\Downloads\gitlab-imports\`, re-create the two junctions
(commands in each SKILL.md), `npm i -g @playwright/cli`, set `API_KEY_21ST`, install Docker Desktop.

---

## 🗺 Weekend Roadmap (Fri 11/20 → Sun 11/22)

**Goals by Sunday:** (1) Phase 1 done: a fresh checkout runs from the README, a coach + 2 clients can log in, and clients
can't see each other's data (tests + playwright-cli walkthrough). (2) The design system exists: `portal/DESIGN.md`,
`base.html`, shared CSS. (3) The public site is built locally. (4) *Stretch:* the HM engine makes a draft plan through the adapter.

### Friday list (slipped into Sat 11/21)
- [x] Restart checks + commit the log
- [x] Dev database decision → Docker + Postgres
- [x] Install WSL + Docker Desktop, verify `hello-world`
- [x] Engine I/O inspection → `portal/ENGINES.md` (baseline: HM 140/140, marathon audit clean except M-5)
- [x] **Django skeleton** in `portal/`: pinned deps, env-var settings, `.env.example`, Postgres in
      `docker-compose.yml`, the project runs locally *(prompt 27)*
- [x] Any remaining repo imports (Kevin): none came in; closed 2026-11-25 (reopen if more arrive)

### Saturday list
- [x] **Models + migrations:** User (role), ClientProfile (incl. **target race: name, date, distance**), TrainingPlan
      (draft/published/archived, generator_version, input_snapshot, generic `plan_type`), ScheduledWorkout (prescription
      only), WorkoutResult (one per workout). One internal unit, with decimals. Registered in Django admin.
- [x] **Auth:** login/logout, password reset (console email in dev), server-side role + ownership checks on every view.
- [x] **Synthetic demo data** command: 1 coach + 2 clients, labeled as fixtures.
- [x] **Isolation tests:** client A can't read or write client B's data; clients can't see drafts.
- [x] **Design system:** taste-skill (kind = service, calm, photo-led) + design-md references → `portal/DESIGN.md`,
      `base.html`, shared CSS tokens.

### Sunday list
- [ ] **Public pages:** Home/Offer, About, Inquiry (form + email to Kevin), Client Login. Check routine + guidelines on each.
- [x] **Client home (read-only):** "This Week" from fixture data, mobile-first. *(prompt 34)*
- [x] **README:** fresh-checkout steps. *(prompt 34, root `README.md`)*
- [x] **Phase 1 sign-off:** fresh clone → README → run → walkthrough as coach, client A, client B.
      **PASSED 2026-11-25** (commit `4e91c8e`): see prompt 34.
- [x] *Stretch:* HM engine adapter → draft plan in the DB. Golden-output engine tests first (`portal/ENGINES.md`). *(prompt 35)*
- [ ] **Commit + push** at the end of each day.

### Needs Kevin this weekend
- Copy for the public pages: offer, pricing/packages (if shown), about/bio, photos (or OK to use licensed stand-ins).

---

## Prompt Log

### Day 1 (2026-11-19), prompts 1–18: setup
Read the brief and the repo, then locked the decisions above. Committed the session-4 strength work. Imported and
installed the toolkit: taste-skill, Vercel web-interface-guidelines, awesome-design-md, playwright-cli and the 21st MCP.
image-to-code was tried and removed, because Claude Code can't generate images. Skills committed in `6a5d184` and pushed.

### Day 2 (2026-11-20), prompts 19–23: environment + DB decision
Fixed a stale environment: Claude was inheriting PyCharm's pre-install PATH, so the cure was to fully exit PyCharm.
All 5 skills tested OK. Dev DB = Docker + Postgres. Log committed (`b28ea69`, `db61278`).

### 24 — 2026-11-21 — Docker verified
WSL 2 (Ubuntu) running; Docker CLI 29.9.3, Compose v5.7.0. Started Docker Desktop (per-user install); `hello-world` passed.
The environment works without the PATH workaround.

### 25 — 2026-11-21 — Engine I/O inspection → `portal/ENGINES.md`
HM 140/140; marathon audit clean except the 7 known M-5 flags. Both engines are pure, deterministic, have no side effects,
and return JSON-safe output in whole miles with no dates. Probe saved as `portal/scripts/probe_engines.py`
(1,638 plans). Findings: the marathon schedule can sum over its weekly target with no warning; neither engine
validates `weeks`; the marathon engine doesn't validate experience or day names; the two engines have different
contracts; dropped sessions only show up as warnings.

### 26 — 2026-11-21 — Engine decisions, TBD file, log cleanup
- Kevin decided plan length (HM 8–20, marathon 12–24), race date (from the client's actual race), and that the race-week
  total includes the race. Recorded in Decisions + `portal/ENGINES.md`.
- Explained "client-facing names" and the "marathon over-count". Both are parked in the new **`TBD.md`** with safe
  defaults, along with the other non-blocking items (self-serve vs coach-led, strength, new-block rules, engine follow-ups,
  later phases).
- Condensed this log: removed the brief recap, resolved items and the day-1 play-by-play (they're still in git history at `db61278`).
- Added the target race to the Saturday ClientProfile model item. Next: the Django skeleton.

### 27 — 2026-11-21 — Django skeleton
- `portal/`: Django 6.1.3 project `config` + apps `accounts` (custom `User`, added before the first migrate so a
  role can be added later without swapping the model) and `core` (placeholder home page). Settings come entirely from
  env vars via django-environ (`portal/.env`, gitignored, with generated secrets; `.env.example` committed). The repo root
  is on `sys.path`, so the engines import unchanged.
- `portal/docker-compose.yml`: `postgres:17.12`, bound to 127.0.0.1 only, named volume, health check. Migrated.
- Hit a hang: `localhost` → IPv6 `::1` stalls on this machine. Fixed with host `127.0.0.1` + `connect_timeout` (Gotchas).
- Verified: `manage.py check` clean, no missing migrations, **5/5 Django tests on Postgres** (home, admin login,
  DB vendor, both engines build a plan from inside Django), HM still **140/140**. playwright-cli at 390px: home +
  admin login render, 0 console errors, no failed requests.
- Kevin still to do: `createsuperuser` (his password, so he runs it).

### 28 — 2026-11-21 — Pushed; plain-English recap
- Pushed master to GitHub (`db61278..` → includes `b6e2be6`, `fcc9da7` and this entry).
- Checked: **no admin account exists yet** (0 users). Kevin still needs to run `createsuperuser`.
- Gave Kevin a plain-English summary of the day.

### 29 — 2026-11-22 — Dev server stopped (low memory)
Claude Code killed the background `runserver` while idle because the PC was low on memory (2.8 GB free of 15.4).
Nothing was lost. Start it on demand only; Docker reserves about 8 GB.

### 30 — 2026-11-22 — Saturday list items 1–4 (commits `0b45d39`, `aba70ce`)
- **Data model:** `User.role` (client by default; superusers become coaches). `ClientProfile` (coach, goals, experience,
  target race, schedule prefs, time zone, units). `TrainingPlan` (status, provenance, `is_fixture`), `PlanWeek` (phase,
  target, engine warnings), `ScheduledWorkout` (prescription, `version`), `PrescriptionRevision` (audit),
  `WorkoutResult` (one per workout, records `prescription_version`). Units: metres and seconds. The client is
  derived from the workout chain, never stored or submitted on results.
- **DB constraints:** one published plan per client; end ≥ start; published ⇒ `published_at`; RPE 1–10; unique
  week numbers and workout slots; results PROTECT workouts from deletion.
- **Access:** `training/access.py` is the single source of who sees what (cross-account requests → 404; wrong role → 403).
  Pages (plain until the design system): `/coach/`, `/me/`, `/plans/<id>/`, `/workouts/<id>/` (result form).
  Auth at `/accounts/` (login, logout, password reset via console email).
- **`seed_demo`** (DEBUG only, re-runnable): `demo_coach`, `demo_client_a` (live plan, hidden draft, 1 result),
  `demo_client_b`. All plans are labeled fixtures. The password is random per run (printed); re-run to get a new one.
- **Tests: 35/35** (isolation across clients and coaches, drafts hidden, result upsert, ignored ownership fields,
  archived = read-only, constraints, login by role, inactive users, password reset email, units, seeding).
- Not yet: `PrescriptionRevision` writing and the publish/archive service (Phase 2); login rate limiting (Phase 3).
- Next: design system (Saturday item 5).

### 31 — 2026-11-22 — Design system (Saturday item 5)
- **Dealt by taste-skill** (service, wellness/fitness trade), from a scratch folder so its finish gate isn't
  armed on the project before Sunday's public page exists. Palette **clay-pine** (cream `#efe9e0`, ink
  `#22261f`, pine `#2e5b44`). The first deal (rose-grey-green) clashed with the KPG logo's cream, so per the skill's
  rule the next was taken, and it matches the logo. Type **Rethink Sans**. Radius soft.
- `portal/static/kairos/kairos.css`: kit-compatible tokens (same names and scales as taste-skill's `system.css`)
  + app components (buttons, cards, split, rows, badges, notices, fields, auth card, fixed header).
  Contrast checked: ink 12.75:1, muted 5.63:1, action 6.45:1, field border 3.39–4.67:1, warn 6.29:1.
- Logo resized from 2.1 MB to 13 KB/50 KB (96/192px) + a 32px favicon. All templates restyled; `nav_cta` block hides
  the header's Client Login button on auth pages.
- **Check routine:** login walkthrough as client and coach at 390 + 1280 (16 screens): 0 overflow, 0 small tap
  targets, 0 console/HTTP errors. Fixed after viewing: narrow coach cards, a stretched workout card, label colons,
  textarea height, "4.20", the field gap, a duplicate primary button, a 42px skip link.
- **web-design-guidelines review:** 9 findings, all fixed (scroll-padding under the fixed header, touch-action,
  long-title wrapping, autofocus off on mobile, curly apostrophes, `translate="no"` on the brand,
  `autocomplete="off"` on result fields, first invalid field focused, a Status error that says what to do).
- `portal/DESIGN.md` written in design-md format (front-matter tokens + sections). Tests still **35/35**.

### 32 — 2026-11-25 (Wed) — Catch-up plan: Sunday's list today, rename to "Hard Left"
- Kevin: do Sunday's list now; **use licensed stand-in photos**; wants to try renaming the brand **"Hard Left"**
  (the hard left turn of running a track).
- Friday + Saturday lists confirmed all ticked (closed the repo-imports item: none came in).
- Name check (web search): no running coach, club or brand called "Hard Left" turned up. Not a trademark search.
  Flagged to Kevin: the phrase also means far-left politics.
- Memory check: 3.1 GB free of 15.4. Top users: Windows services 1.8 GB, Edge 1.8 GB, PyCharm 1.3 GB, WSL/Docker ~1.4 GB.
  Docker isn't the main hog; a WSL cap is cheap insurance, not a cure.
- Waiting on Kevin: rename scope, offer/bio facts for the public pages, OK for the WSL memory cap.

### 33 — 2026-11-25 — Docker memory cap + rename to "Hard Left" (display only)
- **WSL/Docker cap:** `%USERPROFILE%\.wslconfig` → `memory=3GB`, `swap=2GB`, `autoMemoryReclaim=gradual`. Docker
  stopped → `wsl --shutdown` → started. Verified: Docker VM 2.84 GB (was ~7.7), Postgres healthy, data intact.
  Undo: delete the file and run `wsl --shutdown`. (Gotcha: `docker desktop stop|start` works from the CLI.)
- **Rename (display only):** page titles, header, footer, login description, email sender ("Hard Left
  <no-reply@localhost>"), admin header ("Hard Left Admin"); admin's "Kairos" fieldset → "Coaching Role".
  Code identifiers untouched.
- **Logo:** KPG logo copies removed from the portal. taste-skill dealt mark **dots** (random from its service list)
  → inline SVG in the header + `favicon.svg`. Phone header fix: brand 17px, no wrap.
- New test: home and login show "Hard Left" and never "Kairos"/"KPG". **36/36** pass; walkthrough 16/16 screens clean.
- `DESIGN.md` updated (name, mark, known gaps). TBD: trademark search + a real logo before launch.

### 34 — 2026-11-25 — Sunday items that needed no input: This Week, README, Phase 1 sign-off
- **This Week** (client home): the live plan's Mon–Sun with rest days, today marked (`aria-current="date"`), a Next Up
  card (first unlogged run from today), planned vs logged miles, and prev/next week via `?week=` (clamped to the plan;
  bad values fall back). "Today" uses `ClientProfile.timezone`. 6 tests with a frozen clock, incl. UTC vs Auckland.
  Visual fixes after screenshots: the Next Up card layout, the today bar moved into the gutter, a wider date column.
- **README.md** (repo root): 6-step Windows setup, daily start, troubleshooting, docs map, Claude tooling (junction
  commands), Flask generator. New `portal/scripts/make_env.py` writes `.env` with random secrets.
- **Phase 1 sign-off PASSED** on a fresh local clone of `4e91c8e` (own Docker project `kairos-signoff`, port 5433):
  README steps 2–6 ran as written; 42/42 portal tests, HM 140/140; walkthrough 16/16 PASS: coach sees both
  clients and A's draft; A and B each see only their own week; A gets 404 on A's own draft, on B's plan and workout, and
  403 on /coach/; B gets 404 on A's plan and draft, and a POSTed result to A's workout → 404. The only failed requests
  were those 7 deliberate attempts. The test copy (container, volume, folder) was removed afterwards.
- Not covered by the sign-off: cloning from GitHub itself (cloned locally because today's commits weren't pushed yet).

### 35 — 2026-11-25 — Stretch done: HM engine → draft plan in the DB (Phase 2 start)
- **Golden snapshots first** (brief §4.7): `training/golden.py` + `golden/{hm,marathon}.json` (16 + 14 cases incl. range
  edges); `GoldenSnapshotTests`; `manage.py engine_golden [--update]`.
- **Adapter** `training/engines.py`: `PlanRequest` validates (HM 8–20 wk, 4–6 runs/wk, 3 tiers, Mon–Sun days, no start in
  the past, with a "race is only N weeks away" message), counts back from the race week (start = Monday of week 1),
  maps to the engine's own argument names, normalizes HM output (names → `WorkoutType` via one `HM_WORKOUTS` table;
  prescription = the engine's `WORKOUT_GLOSSARY` purpose, effort and style options; miles → metres). Race moved to the
  real race date; a run already on race day is dropped with a warning; race week total = shakeouts + 13.1.
  `generator_version` = `half_marathon_engine_main_4plus_v5_7@<sha256[:12]>`.
- **Service** `training/services.py::generate_draft`: own-coach check, engine run *before* the transaction, then the plan +
  weeks + workouts in one `transaction.atomic()`; `input_snapshot` = request + exact engine kwargs + peak + time.
- **UI:** Clients → **Generate Draft** (`/coach/clients/<id>/generate/`), prefilled from the profile; fieldsets + day-picker
  chips (CSS fixed after screenshots: the generic `.field input/label` rules were overriding the checkboxes).
- **Tests: 64/64** (+22): snapshots, validation, date math, adapter shape, race-day move + clash, glossary text, provenance,
  **failure midway saves nothing**, older plans/results untouched, only the own coach (others 404, clients 403).
- **Browser check:** generated a real 12-week draft for demo client Avery (plan #4 in the dev DB, real engine output, not
  a fixture): race Sun Feb 14 2027 (engine said Sat), race week 19.1 mi, 0 console errors, 0 overflow at 390/1280.
  The draft stays in the dev DB (`seed_demo` only rebuilds fixtures); delete it in admin if unwanted.
