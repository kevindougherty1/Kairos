# Kairos Client Portal — Session Log

Running context file for the portal build session (started 2026-11-19).
I update it after every prompt so we don't lose context. The source brief is
`Kairos_Client_Portal_Implementation_Plan.md`; long-lived engine history is in `KAIROS_CONTEXT.md`.

---

## ▶ START HERE: where we left off (day 2, Fri 2026-11-20, mid-morning)

**Still no portal code.** Day 2 so far (prompts 19–23): restart checks done, all 5 skills tested and
working, log committed (`b28ea69`), and **dev DB decided: Docker Desktop + Postgres**. Kevin is exiting
PyCharm (and rebooting for WSL) to fix the stale-environment problem.

### ▶ Resume here (day 2, after the restart)
1. **Verify the restart fixed the environment.** In a fresh PyCharm terminal → `claude`, check that
   `node --version`, `playwright-cli --version` and `$env:API_KEY_21ST` all work **without** the PATH
   workaround, and that `/mcp` shows `21st` connected. If they don't, PyCharm was still running in the
   background (check Task Manager for `pycharm64.exe`) → reboot.
2. **Install Docker (Kevin runs these; they need admin rights):**
   a. Admin PowerShell: `wsl --install` → **reboot** (if it isn't done before exiting PyCharm).
   b. Install Docker Desktop from docker.com (choose the WSL 2 backend) → start it once and accept the terms.
   c. Claude checks: `docker --version`, `docker compose version`, `docker run --rm hello-world`.
3. **Then continue the Friday list:** engine I/O inspection → `portal/ENGINES.md`, then the Django skeleton
   with a `docker-compose.yml` Postgres service (the Django app itself runs from `.venv`; only Postgres runs in
   the container to start with).

*(Day 1 summary below is still accurate apart from the items marked done.)*

**Day 1 was setup only.** We locked the big decisions and installed the
design and testing toolkit. Phase 1 (Django foundations) has not started.

### Decisions locked (details under "Decisions" below)
- **Django** portal in `portal/`, importing the existing HM + marathon engines unchanged. Flask `app.py` stays.
- **No Wix.** The public site (home/offer, about, inquiry, Client Login) is also Django and ships first.
  *This overrides the brief, which still says Wix. The brief summary below is out of date on that point.*
- **6 v1 plan types:** HM, Marathon (existing engines) + Speed, Base/Economy, Post-race recovery,
  Maintenance (new, so each needs a rules design session with Kevin before code). Plan type is a generic field.
- **Copy:** Title Case headings and buttons, sentence case body.
- **Dev database: Docker Desktop + Postgres** (decided 2026-11-20, prompt 23). Matches the brief's
  "containerized development setup" (`Kairos_Client_Portal_Implementation_Plan.md`, line 37).

### Toolkit installed (all committed in `6a5d184` and pushed to GitHub)
| Skill / tool | Role | How it's installed |
|---|---|---|
| `design-taste-frontend` (taste-skill) | Sets the visual system for public pages and portal | junction → `gitlab-imports\taste-skill` (gitignored) |
| `design-md` | 84 DESIGN.md reference systems; Kairos tokens will live in `portal/DESIGN.md` | wrapper + junction `library/` → `gitlab-imports\awesome-design-md\design-md` |
| `web-design-guidelines` | Vercel UI rules: quality gate before any page is "done" | vendored, rules pinned at `434b7f9` |
| `playwright-cli` | Claude opens pages in headless Edge, screenshots, catches console/network errors and overflow | `npm i -g @playwright/cli` (0.1.25) + version-matched skill; `.playwright/cli.config.json` = msedge |
| `21st-ui` + 21st MCP | Search React components on 21st.dev, **rebuild them as Django + CSS** (never npm/shadcn) | `.mcp.json` (key from user env var `API_KEY_21ST`, already set) + wrapper skill, read-only tools |
- **Precedence:** Kevin's decisions > taste-skill > design-md / 21st components > (gate) web-design-guidelines.
- **"Check my work" routine for every page:** localhost → screenshots at 390 + 1280 → `console` → `requests` →
  overflow check → view screenshots → fix → web-design-guidelines review → only then show Kevin.
- **Removed:** image-to-code (Claude Code can't generate images; replaced by 21st).

### First things to do tomorrow *(day 1 list, all done on day 2)*
1. **Restart check:** confirm `node --version` and `playwright-cli --version` work from PATH. Confirm the
   `21st` MCP server is connected (Kevin approves it if prompted), then run one test `search`.
2. **Commit the uncommitted log entries** (prompt 17 + this summary).
3. **Ask Kevin** if more repo imports are coming, then follow the **Weekend roadmap** below (Friday list).

### Gotchas learned
- Run `playwright-cli` from **PowerShell**, because Git Bash mangles `$APPDATA` paths. It blocks `file://`,
  so test via `http://localhost`. The network command is `requests`.
- Delete a junction with `cmd /c rmdir`, never `Remove-Item -Recurse` (that can wipe the target).
- PowerShell 5.1 `Set-Content -Encoding utf8` adds a BOM, so strip it from files git reads.
- The taste-skill clone is **shallow**, so its git history is incomplete.
- 21st free tier allows only **2 `get_component` calls a day**, so search first and retrieve once. AI generation is off.
- Kevin pasted the 21st key into chat on day 1. He can rotate it at 21st.dev/mcp if he wants.

### Fresh-checkout setup (goes in README during Phase 1)
Clone taste-skill + awesome-design-md into `C:\Users\kevin\Downloads\gitlab-imports\`, re-create the two
junctions (commands in each SKILL.md), `npm i -g @playwright/cli`, set `API_KEY_21ST`.

---

## 🗺 Weekend roadmap: Fri 2026-11-20 → Sun 2026-11-22

Drafted at the end of day 1 as a proposal. Kevin can reorder or cut items. Tick boxes as we go and
note any slip in the prompt log.

### 🎯 Goals by end of Sunday
1. **Phase 1 done**, measured by the brief's own done-check: a fresh checkout runs from the README; a coach
   and 2 clients can log in; clients can't see each other's data (proven by tests *and* a playwright-cli walkthrough).
2. **Kairos design system exists:** `portal/DESIGN.md` (tokens chosen with taste-skill), a base template,
   and shared CSS used by both the public pages and the portal.
3. **Public site built locally:** Home/Offer, About, Inquiry form, Client Login. Each one passes the "check
   my work" routine and the web-design-guidelines review. (Deploying comes later.)
4. **Stretch:** a Phase 2 head start. The HM engine produces a **draft** plan through the adapter, saved
   atomically with `generator_version` + `input_snapshot`, visible to the coach only.

### Friday 11/20: Foundations and engine inspection
- [x] Restart checks: node, playwright-cli, 21st MCP test `search`. Commit the log. *(done prompt 21; PATH caveat in the log)*
- [ ] Finish any remaining repo imports (Kevin).
- [x] **Decision (Kevin): dev database.** → **Docker Desktop + Postgres** (prompt 23).
- [ ] **Install WSL + Docker Desktop** (Kevin, admin + reboot), then Claude verifies with `hello-world`.
- [ ] **Engine I/O inspection** (brief rule: inspect before integrating). For `half_marathon_engine_main_4plus_v5_7.py`
      and `engineV3.py`, document the real inputs, outputs, side effects and determinism. Run `test_engine.py`
      (expect 140/140) and `marathon_audit.py` as the regression baseline. Write it up in `portal/ENGINES.md`.
- [ ] **Django skeleton** in `portal/`: pinned deps, env-var settings, `.env.example`, Postgres
      connection, the project runs locally.

### Saturday 11/21: Data model, auth, design system
- [ ] **Models + migrations:** User (role), ClientProfile, TrainingPlan (draft/published/archived,
      generator_version, input_snapshot, generic `plan_type`), ScheduledWorkout (prescription only),
      WorkoutResult (one per workout). One internal unit for distances and paces. Register them in Django admin.
- [ ] **Auth:** login/logout, password reset (console email backend for dev), and server-side
      role + ownership checks used by every view.
- [ ] **Synthetic demo data** command: 1 coach + 2 clients, clearly labeled as fixtures.
- [ ] **Isolation tests:** client A can't read or write client B's plans, workouts or results; clients
      can't see drafts.
- [ ] **Design system:** run taste-skill (kind = service, calm, photo-led), look at the oura/nike/cal
      references in design-md, write `portal/DESIGN.md`, build `base.html` + shared CSS tokens.

### Sunday 11/22: Public pages, Phase 1 sign-off, stretch
- [ ] **Public pages:** Home/Offer, About, Inquiry (form + email to Kevin), Client Login link. Run the
      check routine at 390/1280 + web-design-guidelines on each.
- [ ] **Client home (read-only):** "This Week" schedule from fixture data, mobile-first.
- [ ] **README:** fresh-checkout steps (incl. skill junctions, playwright-cli, `API_KEY_21ST`).
- [ ] **Phase 1 sign-off:** fresh clone → README → run → playwright-cli walkthrough as coach, client A
      and client B. Record the result here.
- [ ] *Stretch:* HM engine adapter → draft plan in the DB (Phase 2 start).
- [ ] **Commit + push** at the end of each day.

### Needs Kevin this weekend
- The dev database decision (Friday).
- Copy for the public pages: offer, pricing/packages (if shown), about/bio, photos (or OK to use licensed stand-ins).
- Optional: a **rules design session for one new block** (Speed is the best first candidate). Nothing gets
  built for the 4 new blocks until their rules are agreed.

### Not this weekend
Deployment/hosting choice, HTTPS, backups, the API surface (`/api/v1/`), check-ins, notifications,
the 4 new block engines, and strength workflows.

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
- [x] **Recovery and Maintenance blocks added to v1** (approved prompt 3). The full v1 plan-type list:
  1. Half marathon: existing engine
  2. Marathon: existing engine (`engineV3.py`)
  3. Speed block: new; rules to be designed with Kevin
  4. Base / Running economy block: new; rules to be designed with Kevin
  5. Post-race recovery / reverse taper (2–4 wk): new; mostly easy running, leads into the next block
  6. Maintenance / bridge block (open-ended): new; holds fitness at steady volume with light quality
  - Deferred: a 10K plan (overlaps the Speed block) and a return-from-injury block (coach-authored, not generated).
  - The four new blocks have no engine yet. Their training rules get a design session with Kevin
    before any code (the brief says no invented training logic). The portal's plan model should treat
    "plan type" generically so the new blocks slot in without schema changes.

- [x] **No Wix.** Public site built in Django in `portal/` (prompt 6).
- [x] **Design tooling: taste-skill and Vercel web-interface-guidelines, both used** (prompt 7).
  Clones live in `C:\Users\kevin\Downloads\gitlab-imports\`.
- [x] **Copy: Title Case headings and buttons** (prompt 7).
- [x] **Dev database: Docker Desktop + Postgres** (prompt 23, 2026-11-20). Postgres runs in a container
  via `docker-compose.yml`; Django runs from `.venv` at first. Needs WSL 2 (virtualization is already on).

## Pending
- Kevin is importing more repos **before website design starts**. Inspect each one as it arrives.
  Day 1 imports: taste-skill, Vercel guidelines, awesome-design-md, playwright-cli, 21st MCP
  (image-to-code was tried and removed).
- ~~Install Node.js 22+~~ Done: v26.13.1 (prompt 9). Restart Claude Code so PATH picks it up.
- Restart Claude Code → verify node/playwright-cli on PATH and the 21st MCP connection.

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

### 3 — 2026-11-19 — Add Recovery + Maintenance blocks
- Kevin approved both suggested blocks. v1 is now 6 plan types (see Decisions).
- Still waiting on the GitLab repo URLs.

### 4 — 2026-11-19 — Import #1: taste-skill
- Cloned https://github.com/Leonxlnx/taste-skill (GitHub, not GitLab) to
  `C:\Users\kevin\Downloads\gitlab-imports\taste-skill`, outside the Kairos repo. Inspection only:
  nothing installed and no scripts run.
- **What it is:** a Claude Code / Codex "skill" (`design-taste-frontend` v2.5.1, MIT). It's a rulebook
  plus Node 22 tooling that steers an AI agent toward building polished *marketing/company websites*.
  It assigns palettes, fonts and hero layouts by business type, uses real photos and icons, then
  renders the page in headless Chrome at 4 widths and blocks "done" until checks pass. It
  installs a Stop hook (`gate.mjs`) and needs Node 22+ and Chrome.
- **Fit for Kairos:** low for the portal. Its rules are for landing pages (one section per screen,
  hero entrances, photo-led). The portal is a logged-in app made of forms and schedules, so those
  rules would actively fight it. The public site is Wix, so the skill doesn't apply there either. It's
  worth reusing for (a) a single portal login/landing page, or (b) a later replacement of the Wix site.
  Kairos as a "service" kind would get photo-led, calm, no-WebGL treatment.
- **Decision pending:** whether to install it at all. My recommendation: not now; revisit for public pages.

### 5 — 2026-11-19 — Drop Wix? (recommendation given, awaiting Kevin's confirmation)
- Kevin likes taste-skill's design and rules and asked whether to skip Wix entirely.
- **My recommendation: yes, skip Wix.** Build the public site as a small Django app in the same
  project (`portal/`): home/offer, about, inquiry form, Client Login. Use taste-skill for those public
  pages (kind = `service`: photo-led, calm, no WebGL). The portal's logged-in screens reuse the same
  palette and fonts but follow app conventions (forms, lists, mobile-first), not landing-page rules.
  - Why: the public site is about 3–4 pages. One codebase, domain, deploy and bill. "Client Login" is a
    plain internal link with no Wix↔portal account gap. The inquiry form reuses the email setup that
    password reset needs anyway. Better resume story (full-stack, designed, deployed).
  - Costs: Kevin edits copy through code/git, not a drag-and-drop editor. There's no public web presence
    until hosting is live (mitigation: deploy the public pages first as an early milestone).
    SEO is basic but fine for a local 1:1 coach.
- Environment check: **Node.js is not installed** (taste-skill needs Node 22+). Edge is present, which
  the skill accepts in place of Chrome. Install Node only when we reach public-page design.
- If confirmed, this changes the brief's §2 system boundaries (no Wix). Record that in the decisions.

### 6 — 2026-11-19 — No Wix confirmed; Import #2: Vercel web-design-guidelines
- **DECISION: No Wix.** The public site (home/offer, about, inquiry, Client Login) is built in Django in
  `portal/`, designed with taste-skill. This overrides the brief's §2 Wix boundary and the
  "Wix public website" row. Public pages ship as an early deploy milestone.
- Node.js is free: open source (MIT), from nodejs.org. Install the LTS release (22+) when needed.
- Cloned `vercel-labs/agent-skills` to `C:\Users\kevin\Downloads\gitlab-imports\agent-skills`. It
  holds 9 skills, mostly React/Next/Vercel-specific. The one Kevin asked about is
  `skills/web-design-guidelines`. It's a thin skill: it fetches its rules at review time from
  `vercel-labs/web-interface-guidelines/command.md`. I also cloned that repo to
  `C:\Users\kevin\Downloads\gitlab-imports\web-interface-guidelines` and read all the rules.
- **What it is:** a UI *review checklist* (about 100 rules) that audits code and reports `file:line` findings. It covers
  accessibility, focus states, forms, animation, typography, long/empty content, images, performance,
  URL state, touch, safe areas, dark mode, locale, hover states, copy and anti-patterns.
  No scripts and no Node.
- **Fit for Kairos:** high, especially for the portal. Its Forms, accessibility and mobile/touch rules are
  exactly what the client result-entry and coach editing screens need. It complements taste-skill:
  taste-skill decides *how pages look*, this one checks *that they work for everyone*.
  - Not applicable (React-only): hydration safety, `useState`/nuqs, `htmlFor` JSX naming,
    virtualization libraries. Django templates get the HTML equivalents.
  - One conflict to settle: Vercel wants Title Case on headings/buttons; taste-skill favors plain
    copy. Pick one copy style for the whole site.
  - Relevant to us: use `Intl.DateTimeFormat` for dates in JS, `tabular-nums` for mileage/pace columns,
    destructive actions (delete plan) need confirmation/undo, URL reflects state (week selector in
    query params), inline field errors with focus on the first error.
- Plan: run it as a review pass on every portal template before each phase's "done" check.

### 7 — 2026-11-19 — Copy style + use both design tools
- **DECISION: Title Case for headings and buttons** (Vercel/Chicago style, e.g. "Log Workout",
  "Publish Plan"). This overrides taste-skill's plain-copy casing. Body text stays sentence case.
- **DECISION: Use both tools together, everywhere.** Kevin's intent: neither tool is optional.
  - **taste-skill** sets the visual system (palette, type pairing, layout, photos, motion, micro-
    interactions) for the public pages *and* the portal. The portal reuses its tokens and design
    rules. Only the rules that are specifically about marketing pages (one section per screen, hero
    entrance, a "moment" per page) are relaxed on logged-in app screens.
  - **Vercel web-interface-guidelines** is the quality gate for all pages: accessibility, forms,
    focus, mobile/touch, copy rules, anti-patterns.
  - Where they conflict, Kevin's decisions win (Title Case so far). Otherwise both apply.

### 8 — 2026-11-19 — Installed both skills into the project
- `.claude/skills/design-taste-frontend` is a **directory junction** to
  `C:\Users\kevin\Downloads\gitlab-imports\taste-skill\skills\taste-skill` (upstream commit `f6b7657`).
  Same approach as the repo's own `install.sh`: `git pull` in the clone updates it in place. It's
  35 MB / 1,631 files, so it's **gitignored, not vendored**. A fresh checkout needs the clone and the
  junction re-created (document in the README later).
- `.claude/skills/web-design-guidelines/` contains SKILL.md (adapted), `rules.md` (upstream
  `command.md` pinned at `434b7f9`) and LICENSE (MIT). It reads the local rules instead of fetching
  them from the web, and adds Kairos notes (Django mappings, skip React-only rules, Title Case).
  This one is committed.
- Also gitignored `.claude/settings.local.json` (machine-local permissions).
- Claude Code detected both skills (`design-taste-frontend`, `web-design-guidelines`).
- **Caveat:** taste-skill's Stop hook runs `node gate.mjs` while the skill is active. Without
  Node installed, that check will error instead of running. **Install Node 22 LTS before the first design task.**

### 9 — 2026-11-19 — Node.js verified
- Node **v26.13.1** and npm 11.20.0 are installed at `C:\Program Files\nodejs\`, which meets taste-skill's 22+
  requirement. The install added it to the system PATH (registry).
- The current Claude Code session started before the install, so its shell doesn't see `node` yet.
  **Restart Claude Code** so the shell and the taste-skill Stop hook pick it up. Until then, call
  it by its full path.
- Pending item "Install Node.js" is done.

### 10 — 2026-11-19 — New session, re-read log
- Re-read this log to restore context in a new session. No code changes.
- `node` is **still not on PATH** in this shell, so the restart didn't pick it up. Use
  `C:\Program Files\nodejs\node.exe` or restart again before the first taste-skill task.
- The prompt 8 work is still uncommitted (`.gitignore`, this log, `.claude/`).

### 11 — 2026-11-19 — Import #3: awesome-design-md, installed as a skill
- Cloned https://github.com/VoltAgent/awesome-design-md to
  `C:\Users\kevin\Downloads\gitlab-imports\awesome-design-md` (commit `fcc7028`, MIT). Markdown and
  yml only, no scripts.
- **What it is:** 84 `DESIGN.md` files (Google Stitch format), each one a writeup of a real site's
  design system: YAML tokens (colors, type, spacing, radii) plus sections on layout, breakpoints, touch
  targets, components, and do's and don'ts. It's a reference library and ships no skill.
- **Installed** as `.claude/skills/design-md/`: a committed `SKILL.md` + `LICENSE`, and `library/`,
  a gitignored directory junction to the clone's `design-md/` folder (same pattern as taste-skill).
  Claude Code detected the skill.
- **How Kairos uses it:** (1) Kairos's own visual system gets written as `portal/DESIGN.md` in this
  format, as the single source of truth for tokens. (2) Entries are reference only: borrow the
  reasoning, never a brand's palette, proprietary fonts or logos. Most relevant: oura, nike, apple,
  airbnb, cal (scheduling), linear.app/notion (app screens), stripe/wise (forms, numbers).
- **Precedence:** Kevin's decisions > taste-skill (picks the system) > design-md (informs and
  documents it); web-design-guidelines gates every page.

### 12 — 2026-11-19 — Import #4: image-to-code (found, install decision pending)
- Kevin named only "image-to-code". Search turned up three repos with that skill: nexu-io/open-design
  (a vendored copy whose metadata lists taste-skill as upstream), plugin87/ux-ui-agent-skills
  (a different skill that needs that whole kit), and the original. It used to live in
  Leonxlnx/taste-skill and moved out in v2.1.1 (2026-10-18) to **Leonxlnx/imagegen-skills** (MIT,
  same author). Our taste-skill clone is shallow, so its history didn't show this.
- Cloned to `C:\Users\kevin\Downloads\gitlab-imports\imagegen-skills` (commit `beb16b0`). Markdown
  only, plus a frontmatter test. Four skills: `image-to-code` (1,228 lines), `imagegen-frontend-web`,
  `imagegen-frontend-mobile`, `brandkit`.
- **What image-to-code does:** it generates design images for each page section first, studies them,
  pulls out text, type, spacing, colors and components, then builds the page to match. Image-first
  is *mandatory* for visual tasks ("IMAGE_GENERATION_EAGERNESS: 10"), and it's written for Codex.
- **Blocker:** the README says it "needs an agent that can both generate images and write code."
  **Claude Code can't generate images.** It *can* read images, so the useful part for us is the
  extraction rules (§20–28), applied to a comp or screenshot that Kevin supplies.
- Its hero and anti-slop rules overlap taste-skill's. Where they conflict, taste-skill should win.
- Asked Kevin how to install it.
- **DECISION: reference-image mode.** Installed `.claude/skills/image-to-code/`. The committed
  `SKILL.md` + `LICENSE` form a wrapper, and `upstream/` is a gitignored junction to the clone's
  `skills/image-to-code`. The skill is manual-only (`disable-model-invocation: true`), so it runs
  only when Kevin asks for it.
  - Kevin supplies images: comps from ChatGPT Images or similar (prompted with the sibling
    `imagegen-frontend-web`/`-mobile` rules, one large image per section), screenshots, or mockups.
    Suggested home: `portal/design-refs/`.
  - Claude applies only the analysis/extraction sections (§8–9, 16–17, 19–28, 34–35), skips the
    generation mandates (§2–7, 10–12, 18), maps results onto `portal/DESIGN.md` tokens, then runs
    web-design-guidelines.
  - Precedence: Kevin > taste-skill > the supplied image > (gate) web-design-guidelines.
- The other three imagegen skills are **not installed**. They're prompt writers for an external
  image tool and stay in the clone.

### 13 — 2026-11-19 — Import #5: microsoft/playwright-cli
- Cloned https://github.com/microsoft/playwright-cli to
  `C:\Users\kevin\Downloads\gitlab-imports\playwright-cli` (commit `c872a33`, Apache-2.0, npm
  `@playwright/cli` 0.1.25, built on Playwright 1.66 alpha, Node 20+).
- **What it is:** unlike the earlier imports, this is a real tool. It's a token-efficient command-line
  driver for a browser (`open`, `goto`, `snapshot`, `click e15`, `fill`, `screenshot`, `resize`,
  sessions, tracing, video, request mocking, test generation), plus a 497-line skill teaching an agent
  to use it. It's headless by default, can use the installed Edge (`--browser=msedge`), and
  `playwright-cli show` opens a dashboard to watch or take over sessions.
- **Install model:** the skill is useless without the CLI. The supported path is
  `npm install -g @playwright/cli@latest`, then `playwright-cli install --skills`. That copies the
  skill matching the CLI version into `.claude/skills/playwright-cli/`, and the CLI warns when the
  two drift apart. So a junction to the git clone (ahead of the npm release) is the wrong pattern here.
- **Fit for Kairos:** high. It lets Claude check the portal in a real browser: log in as coach vs.
  client, confirm isolation (Phase 1 done-check), walk the generate→publish→log-result loop
  (Phase 2), and take screenshots at phone widths for the web-design-guidelines review. It's
  separate from the committed test suite, which should use Python `pytest-playwright` in CI. Claude in
  Chrome drives Kevin's real browser. playwright-cli is the isolated, headless option.
- Asked Kevin to approve the global npm install.
- **DECISION: install it and use Edge.** Ran `npm install -g @playwright/cli@latest` (0.1.25, at
  `%APPDATA%\npm`), then `playwright-cli install --skills`. That:
  - copied the version-matched skill to `.claude/skills/playwright-cli/` (SKILL.md + 10 references,
    committed, not a junction). Claude Code detected it.
  - created `.playwright/cli.config.json` (chromium, channel `msedge`; committed), so no browser download.
  - added `.playwright-cli/` (snapshots/output, "may contain credentials") to `.gitignore`.
  - downloaded ffmpeg + winldd (~1.7 MB) to `%LOCALAPPDATA%\ms-playwright\`.
- Smoke test passed: headless Edge opened a test page; snapshot (heading + "Log Workout" button refs),
  eval and close all worked.
- PATH: Node and `%APPDATA%\npm` are both in the persistent PATH, but this session's shell
  predates them, so calls need them prepended until Claude Code restarts.
- Update: `npm install -g @playwright/cli@latest`, then `playwright-cli install --skills` again.
  Undo: `npm uninstall -g @playwright/cli`.

### 14 — 2026-11-19 — Confirmed playwright-cli is the right tool (demo)
- Kevin's goal: Claude opens a browser, screenshots what it just built, and catches messy output and
  errors before Kevin sees them. playwright-cli does exactly that. Proven on a deliberately broken
  test page, served from localhost at phone size (390×844):
  - `console` caught the JS `ReferenceError` + 404s (missing image, API call, favicon)
  - `requests` listed the failed requests with their status codes
  - `eval` measured a 932px-wide row on a 390px screen (horizontal scroll bug)
  - `screenshot` captured it, and Claude viewed the image: cut-off row, broken image icon
- Gotchas: `file://` pages are blocked by default (fine, since the portal is served via
  `http://localhost`). The network command is `requests`, not `network`. From Git Bash, `$APPDATA`
  paths get mangled, so run playwright-cli from PowerShell (or after a restart, from PATH).
- **Planned "check my work" routine for every page I build:** open on localhost → screenshots at
  390 and 1280 widths → `console` (zero errors/warnings) → `requests` (no 4xx/5xx) → overflow check →
  view the screenshots → fix → then web-design-guidelines review. Only then show Kevin.

### 15 — 2026-11-19 — Removed image-to-code; Import #6: 21st.dev MCP
- **DECISION: image-to-code removed** (replaced by 21st). I removed the junction first with
  `rmdir`, so the target was untouched, then deleted `.claude/skills/image-to-code/`, the
  `imagegen-skills` clone and its `.gitignore` line. Prompt 12 is now history only.
- Cloned https://github.com/21st-dev/magic-mcp to `C:\Users\kevin\Downloads\gitlab-imports\magic-mcp`
  (commit `6b5299e`, ISC). "Magic MCP" is now the **21st MCP**: a hosted HTTP MCP server at
  `https://21st.dev/api/mcp` with an `x-api-key` header. Old Magic keys were reset. Tools: `search`,
  `get_component`, `get_inspiration`, `search_logo`, and `generate`/`iterate_generation` (only with paid
  hosted AI). Free tier: catalog search + **2 component retrievals a day**.
- **Stack mismatch:** the components are React + Tailwind/shadcn, and Kairos is Django templates +
  plain CSS/JS. Upstream's skill says to `shadcn add`/install, which is wrong for us.
- **Installed:**
  - `.mcp.json` (project scope, committed): server `21st`, key from `${API_KEY_21ST}`. No
    secret in the file.
  - `.claude/skills/21st-ui/` (committed SKILL.md + LICENSE): a Kairos wrapper of upstream's skill.
    It never runs npm/shadcn or writes .tsx. Components are references, rebuilt as Django templates +
    CSS on Kairos tokens + vanilla JS. Search first, retrieve sparingly. Ask before any AI-credit call.
    Precedence: Kevin > taste-skill > 21st components > (gate) web-design-guidelines. Claude Code
    detected the skill.
  - Not installed as the upstream Claude plugin, because its bundled skill would push React installs.
- Endpoint probe without a key → 401, as expected. **Waiting on Kevin:** create a key at
  21st.dev/mcp, set it as user env var `API_KEY_21ST`, restart Claude Code, approve the `21st`
  project MCP server when prompted.

### 16 — 2026-11-19 — 21st API key set and verified
- Saved Kevin's key as Windows **user** env var `API_KEY_21ST` (registry only, in no file).
- Direct test against `https://21st.dev/api/mcp`: `initialize` 200, `tools/list` 200, 50 tools.
  `generate` isn't listed, so hosted AI generation is **off** (free plan, as expected).
- The tool list includes account-changing tools (submit/edit/delete component, edit_profile, video_*,
  bookmarks, teams). Added a **read-only by default** rule to the `21st-ui` skill.
- **Still to do:** restart Claude Code so it reads the env var, approve the `21st` MCP server, then
  run a test `search` through MCP.

### 17 — 2026-11-19 — Committed the skills work
- Commit `6a5d184` on master (local, not pushed): 4 skills (web-design-guidelines, design-md,
  playwright-cli, 21st-ui), `.mcp.json`, `.playwright/cli.config.json`, `.gitignore`, log prompts 8–16.
  22 files.
- Checked first: the 21st key is in no tracked file. Junctions (taste-skill, design-md library) and
  `.claude/settings.local.json` stay ignored.
- Fresh checkout needs: the gitlab-imports clones + 2 junctions re-created, `npm i -g @playwright/cli`,
  and `API_KEY_21ST` set. That goes in the README when Phase 1 creates it.

### 18 — 2026-11-19 — Pushed; end-of-day summary + weekend roadmap
- Pushed master `5bd4df5..6a5d184` (it also carried the two unpushed prompt-2 commits).
- Added the **START HERE** summary and the **Weekend roadmap** (Fri–Sun goals and daily checklists) at the
  top of this file. Saved a Claude memory pointing future sessions here.
- Log changes since `6a5d184` are not committed yet (first task Friday).

### 19 — 2026-11-20 — "run /mcp" (MCP status check)
- `/mcp` is a built-in CLI command; Claude can't run it, so Kevin has to type it.
- Status seen from the session: `claude-in-chrome` and claude.ai **Claude Docs** are connected. **`21st`
  is not**: it only offers `authenticate` / `complete_authentication`, so the API key wasn't sent.
- Cause: `API_KEY_21ST` is set in the user registry but **not in the Claude Code process**, so
  `${API_KEY_21ST}` in `.mcp.json` expanded to empty. The terminal Claude was launched from predates the
  env var. Fix: close the terminal window completely, open a new one, start `claude` again, then `/mcp`.

### 20 — 2026-11-20 — Day 2 start: Friday plan read back
- `/mcp` after the terminal restart: **21st connected** (prompt 19 fix worked).
- Read START HERE + Weekend roadmap and gave Kevin the Friday plan. No code changes yet.

### 21 — 2026-11-20 — Restart checks + commit the log
- **Tools are installed and work:** node v26.13.1, npm 11.20.0, playwright-cli 0.1.25.
- **Caveat: this Claude Code process still has the old environment.** `node`/`playwright-cli` aren't on the
  session PATH, and `API_KEY_21ST` isn't in the process either, although both are saved in the registry
  (Machine PATH has `C:\Program Files\nodejs\`, User PATH has `%APPDATA%\npm`). Whatever launched Claude
  was opened before day 1's installs. **Workaround** (until a full sign-out or reboot): start PowerShell
  commands with
  `$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')`.
- **21st MCP is connected through OAuth sign-in** (the `/mcp` "Signed in" step), not the API key header.
  Test `search` ("workout schedule card") returned 3 components. That used no `get_component` quota.
  The read-only rule in `21st-ui` still applies.
- Committed the log (prompts 17–21, START HERE, weekend roadmap). Friday checkbox 1 ticked.

### 22 — 2026-11-20 — PATH root cause, skills readiness check, dev DB options explained
- **Stale PATH root cause:** Claude runs inside PyCharm's terminal (claude.exe → powershell → pycharm64.exe,
  PyCharm started 11/19 15:34, before Node and the key were installed). New terminal tabs inherit PyCharm's
  old environment. **Fix:** fully exit PyCharm (File → Exit) and reopen, or reboot.
- **API key:** no reset needed. 21st is connected through OAuth sign-in. After the PyCharm restart, the key
  header will be sent too. Rotating it (it was pasted in chat on day 1) is optional.
- **Skills readiness check, all 5 OK:** each has a SKILL.md; both junctions resolve (taste-skill,
  design-md library = 84 systems); web-design-guidelines rules.md present; 21st search works.
  playwright-cli smoke test on a localhost page: page opened in Edge, title read, console log captured.
  Clones in gitlab-imports: agent-skills, awesome-design-md, magic-mcp, playwright-cli, taste-skill,
  web-interface-guidelines.
- **Gotcha:** `Start-Process python` fails (Windows Store alias). Use `.venv\Scripts\python.exe`.
  The repo already has a `.venv` (Python 3.14.6).
- **DB machine check:** no Docker, no Postgres, WSL not installed; virtualization is ON (hypervisor
  running); 15.4 GB RAM, 390 GB free. Explained Docker vs local Postgres to Kevin; waiting on his choice.

### 23 — 2026-11-20 — Save state before PyCharm exit; dev DB = Docker
- **Decision: Docker Desktop + Postgres** (option A). Added to Decisions + START HERE, Friday box ticked,
  new box for the WSL + Docker install.
- Rewrote **START HERE** with a "Resume here" list: verify the env after the restart → Kevin installs WSL
  (`wsl --install`, reboot) + Docker Desktop → Claude runs `hello-world` → engine inspection → Django skeleton.
- Explained to Kevin that "the brief" = `Kairos_Client_Portal_Implementation_Plan.md` (the planning
  handoff from 11/19; "containerized development setup" is on line 37).
- Committed the log before the restart.
