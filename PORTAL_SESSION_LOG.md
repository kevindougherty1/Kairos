# Kairos Client Portal: Session Log

Running context for the portal build (started 2026-11-19), updated after every prompt.
- Brief: `Kairos_Client_Portal_Implementation_Plan.md`. Decisions below override it (e.g. the brief still says Wix).
- Engine history: `KAIROS_CONTEXT.md`. Engine contract for the portal: `portal/ENGINES.md`.
- Parked items (not this weekend): `TBD.md`.

---

## ▶ START HERE (Sat 2026-11-21, evening)

**Friday list done: the Django skeleton runs on Postgres in Docker.** Phase 1 data model starts next.

### Resume here
1. **Start Docker Desktop first** (per-user install: `%LOCALAPPDATA%\Programs\DockerDesktop\Docker Desktop.exe`).
   Then, from `portal/`: `docker compose up -d` → `..\.venv\Scripts\python.exe manage.py runserver` → http://127.0.0.1:8000/
2. **Kevin:** create the admin login (once): `.venv\Scripts\python.exe portal\manage.py createsuperuser`.
3. **Next: Saturday list**, starting with models + migrations (User role, ClientProfile with target race, ...).

---

## Decisions

| Area | Decision |
|---|---|
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
- [ ] Any remaining repo imports (Kevin), if there are any

### Saturday list
- [ ] **Models + migrations:** User (role), ClientProfile (incl. **target race: name, date, distance**), TrainingPlan
      (draft/published/archived, generator_version, input_snapshot, generic `plan_type`), ScheduledWorkout (prescription
      only), WorkoutResult (one per workout). One internal unit, with decimals. Registered in Django admin.
- [ ] **Auth:** login/logout, password reset (console email in dev), server-side role + ownership checks on every view.
- [ ] **Synthetic demo data** command: 1 coach + 2 clients, labeled as fixtures.
- [ ] **Isolation tests:** client A can't read or write client B's data; clients can't see drafts.
- [ ] **Design system:** taste-skill (kind = service, calm, photo-led) + design-md references → `portal/DESIGN.md`,
      `base.html`, shared CSS tokens.

### Sunday list
- [ ] **Public pages:** Home/Offer, About, Inquiry (form + email to Kevin), Client Login. Check routine + guidelines on each.
- [ ] **Client home (read-only):** "This Week" from fixture data, mobile-first.
- [ ] **README:** fresh-checkout steps.
- [ ] **Phase 1 sign-off:** fresh clone → README → run → walkthrough as coach, client A, client B. Record the result here.
- [ ] *Stretch:* HM engine adapter → draft plan in the DB. Golden-output engine tests first (`portal/ENGINES.md`).
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
