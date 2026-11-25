# Hard Left

1:1 running coaching: a client portal where the coach generates, reviews and publishes training plans,
and clients see their week and log their runs. ("Kairos" is the project's code name; you'll see it in
folders and file names.)

| Folder / file | What it is |
|---|---|
| `portal/` | **The client portal** (Django 6.1 + PostgreSQL). Start here. |
| `engineV3.py`, `half_marathon_engine_main_4plus_v5_7.py` | The marathon and half-marathon plan engines. The portal imports them unchanged. |
| `app.py`, `templates/`, `static/` | The original Flask plan generator (still works, separate from the portal). |
| `test_engine.py`, `marathon_audit.py` | Engine regression checks. |

## Run the Portal on Windows (Fresh Checkout)

**You need:** Git, Python 3.14 (`py --list` shows it), and Docker Desktop (WSL 2 backend). All commands are
PowerShell, run from the repo root unless noted.

```powershell
# 1. Get the code
git clone https://github.com/kevindougherty1/Kairos.git
cd Kairos

# 2. Python environment and packages
py -3.14 -m venv .venv
.venv\Scripts\python.exe -m pip install -r portal\requirements.txt

# 3. Settings: creates portal\.env with random secrets (gitignored, never commit it)
.venv\Scripts\python.exe portal\scripts\make_env.py

# 4. Database: open Docker Desktop first, then
cd portal
docker compose up -d                 # Postgres 17 on 127.0.0.1:5432, wait until it says Started

# 5. Tables, your admin login, demo data
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py createsuperuser      # you choose the password; superusers are coaches
..\.venv\Scripts\python.exe manage.py seed_demo            # 1 demo coach + 2 demo clients; prints their password

# 6. Run it
..\.venv\Scripts\python.exe manage.py runserver
```

Open http://127.0.0.1:8000/. Log in as `demo_coach`, `demo_client_a` or `demo_client_b` (the password
`seed_demo` printed), or as your own admin at http://127.0.0.1:8000/admin/.

**Run the tests** (from `portal\`, Docker running): `..\.venv\Scripts\python.exe manage.py test`

### Every Day After That

1. Open Docker Desktop.
2. In `portal\`: `docker compose up -d`, then `..\.venv\Scripts\python.exe manage.py runserver`.

### When Something Goes Wrong

| Symptom | Fix |
|---|---|
| `failed to connect to the docker API … docker_engine` | Docker Desktop isn't running. Open it and wait a few seconds. |
| Django hangs on any database command | Use `POSTGRES_HOST=127.0.0.1` in `portal\.env`, not `localhost` (on some PCs localhost tries IPv6 first and stalls). |
| `Set POSTGRES_PASSWORD in portal/.env` | Step 3 was skipped. Run `make_env.py`. |
| Port 5432 already in use / a second copy of the portal | In that copy's `portal\.env` set `COMPOSE_PROJECT_NAME=kairos2` and `POSTGRES_PORT=5433`. |
| `python` opens the Microsoft Store | Use `.venv\Scripts\python.exe` (or `py -3.14`) as shown above. |
| Start over with an empty database | In `portal\`: `docker compose down -v` (**deletes all local data**), then steps 4–5. |

## Project Docs

| File | Read it for |
|---|---|
| `PORTAL_SESSION_LOG.md` | Where the build is and every decision made. **"START HERE" at the top.** |
| `portal/ENGINES.md` | How the plan engines behave and how the portal will call them. |
| `portal/DESIGN.md` | The design system: colours, type, components, rules. |
| `TBD.md` | Parked questions and later work. |
| `Kairos_Client_Portal_Implementation_Plan.md` | The original brief (the session log's decisions override it). |
| `KAIROS_CONTEXT.md` | Engine history and coaching logic. |

## Optional: the Claude Code Tooling

The design and browser-testing skills in `.claude/skills/` work without extra setup except these three:

1. **taste-skill and the design-md library** are folder links (junctions) to clones outside the repo:
   ```powershell
   $imp = "C:\Users\kevin\Downloads\gitlab-imports"
   git clone https://github.com/Leonxlnx/taste-skill.git "$imp\taste-skill"
   git clone https://github.com/VoltAgent/awesome-design-md.git "$imp\awesome-design-md"
   New-Item -ItemType Junction -Path .claude\skills\design-taste-frontend -Target "$imp\taste-skill\skills\taste-skill"
   New-Item -ItemType Junction -Path .claude\skills\design-md\library -Target "$imp\awesome-design-md\design-md"
   ```
   To remove a junction, use `cmd /c rmdir <path>`. Never `Remove-Item -Recurse`, which can delete the clone it points to.
2. **Browser checks:** `npm i -g @playwright/cli` (Node 22+). It uses the installed Edge.
3. **21st.dev components:** set the user environment variable `API_KEY_21ST`, then restart the terminal.

## The Original Flask Generator

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py        # http://127.0.0.1:5000/
.venv\Scripts\python.exe test_engine.py      # half marathon engine: expect 140/140
```
