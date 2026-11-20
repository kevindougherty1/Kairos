# Kairos Coaching Platform — Agent Implementation Brief

Prepared for Kevin Dougherty · November 19, 2026

## 1. Goal and agreed direction

Build a custom client portal for Kairos, a future 1:1 running and strength coaching business. Keep Wix as the public business website. Connect the two with a **Client Login** link leading to the separately hosted portal.

The portal should let Kevin generate, review, edit, and assign training plans, while clients can view their own workouts and record results. The existing Python training-plan generator is the starting point for plan generation. Coaching decisions remain with Kevin; generated plans are drafts until he publishes them.

This project also supports Kevin's backend engineering development: Django, APIs, relational databases, cloud deployment, and reliable data workflows. Start with a practical product for approximately 2–3 clients and one coach.

**Status:** This is a planning handoff, not a description of an implemented application. Wix plus a custom Django portal is the discussed direction. The specific stack and implementation details below are proposed defaults for the development agent.

## 2. System boundaries

| Component | Responsibility |
| --- | --- |
| Wix public website | Homepage, coaching offer, about page, inquiries, and a Client Login link |
| Custom portal frontend | Login, client training schedule, workout details, results entry, and coach management screens |
| Django backend | Authentication, authorization, validation, business logic, generator integration, and persistence |
| PostgreSQL | Client profiles, plans, scheduled workouts, results, and check-ins |
| Existing Python generator | Produce a proposed running plan from validated inputs |

Illustrative addresses: `www.yourbrand.com` for Wix and `app.yourbrand.com` for the portal. No domain has been selected or verified by this brief.

Django runs on separate Python-capable hosting. Do not attempt to upload the Python application into Wix's Node.js backend. For the initial version, Wix only links to the portal. Wix accounts, payments, and portal authentication are not automatically synchronized; shared login and billing integration are outside the initial scope.

## 3. Proposed technical defaults

- Use a single Django application with PostgreSQL.
- Use Django templates, HTML, CSS, and limited JavaScript for the first frontend. Start with a suitable licensed responsive template; a separate React application is not required.
- Add Django REST Framework for a small versioned API covering plans and workout results. Share business logic between API views and template views.
- Use Django session authentication and CSRF protection for the browser portal. Establish server-side coach/client authorization and object ownership checks.
- Use Django admin for initial internal data management, then add a small coach dashboard where it improves the coaching workflow.
- Keep generation logic in a standalone Python module behind an application service rather than embedding it into HTTP views.
- Provide a containerized development setup, dependency lock/pin strategy, environment-variable configuration, database migrations, and automated CI checks.
- Select maintained, compatible dependency versions at implementation time and document them.
- Choose the production host after checking repository constraints, deployment support, and operating cost. Cloud provider is not yet decided. Managed PostgreSQL is preferred for launch.
- Defer Kubernetes and distributed services. They may be useful later as learning exercises but are unnecessary for the first small roster.

## 4. Existing generator integration

Kevin has an existing Python marathon-plan generator. A previously identified filename is `engineV3.py`; its current source has **not** been inspected for this brief. Obtain the authoritative current file/repository before integration. Do not assume its function names, schema, dependencies, supported race distances, or present behavior.

The agent should:

1. Read repository instructions and inspect the generator's actual inputs, outputs, dependencies, and side effects.
2. Preserve existing training rules while separating reusable generation logic from scripts or interactive prompts if necessary.
3. Add an adapter that accepts validated application inputs and returns structured plan data.
4. Record the generator version and input snapshot with each generated plan.
5. Save a complete generated draft atomically. A failure must not leave a partially created plan.
6. Preserve previous plans and client workout results when generating a new draft.
7. Add regression tests around the existing generator's important rules before changing its structure.

If source access is missing, continue building accounts, models, and portal screens with clearly labeled fixtures. Do not silently replace the generator with invented training logic or present fixture plans as real outputs.

## 5. First release scope

### Coach workflow

1. Create or invite a client account and assign that client to Kevin.
2. Enter/review goals, training background, available training days, and relevant scheduling preferences.
3. Generate a draft plan using the existing engine's supported inputs.
4. Review and edit scheduled workouts.
5. Publish the plan so it becomes visible to its assigned client.
6. Review workout completion, results, and feedback; adjust upcoming workouts.

### Client workflow

1. Activate the account or securely set a password, log in, and reset a forgotten password.
2. View the current published plan in a mobile-friendly weekly schedule.
3. Open a workout to see its prescription and coach notes.
4. Record completion status, actual distance/duration where relevant, perceived effort, and comments.
5. Review previous workout results.

### Initial screens

- Login, account activation, and password reset.
- Client dashboard with this week's training and next workout.
- Workout details and result-entry form.
- Coach client list and individual client detail.
- Draft plan generation, editing, and publishing screens.

A simple weekly list is sufficient before a complex interactive calendar. Prefer clear forms and accessible mobile layouts over elaborate visual effects.

## 6. Suggested relational model

| Entity | Core fields and relationships |
| --- | --- |
| User | Authentication identity, active status, role |
| ClientProfile | User, assigned coach, goals, training background, preferences, timezone and preferred units |
| TrainingPlan | Client, title, start/end dates, draft/published/archived status, creator, generator version, input snapshot |
| ScheduledWorkout | Plan, scheduled date, workout type, prescription, target distance/duration where applicable, coach notes |
| WorkoutResult | Scheduled workout, client, completion status, actual performance, perceived effort, comments, timestamps |
| WeeklyCheckIn — next phase | Client, week, recovery/adherence feedback, client notes, coach response |

Use foreign keys and database constraints. Store measurable values in a consistent internal unit with explicit conversion at the interface. Preserve the prescription and actual performance as separate data. Define date/time handling explicitly for client schedules.

Do not allow clients to set their own coach, role, plan owner, or publication status through submitted fields. Keep a minimal revision/audit record of published prescription changes so old results remain understandable.

## 7. Minimum API surface

Proposed routes; adapt naming to the repository while retaining these boundaries:

- `GET /api/v1/me/` — current user's profile.
- `GET /api/v1/plans/` — only plans the caller is authorized to see.
- `GET /api/v1/plans/{id}/` — authorized plan detail and workouts.
- `PUT /api/v1/workouts/{id}/result/` — create/update the client's own result without duplication.
- `POST /api/v1/clients/{id}/plans/generate/` — coach-only generation of a draft.
- `POST /api/v1/plans/{id}/publish/` — coach-only publication after validation.

Clients see only their own published plans and results. Coaches can manage only their assigned clients. Enforce this on every read and write, not just by hiding buttons. Version the API and add contract tests before making response changes that could break clients.

## 8. Build sequence and acceptance criteria

### Phase 1 — Inspect and establish foundations

Inspect source, document generator integration, create the Django project, PostgreSQL models, migrations, authentication, and development setup.

**Done when:** A fresh checkout can be started from the README; migrations work; a coach and two test clients can log in; one client cannot access the other's data.

### Phase 2 — Complete the core coaching loop

Integrate the real generator, draft/edit/publish workflow, client schedule, and workout result entry.

**Done when:** Kevin can generate and edit a draft, publish it to one client, and review that client's logged workout. Drafts remain hidden from clients. Repeated result submissions do not create duplicates. Regeneration preserves existing published data and results.

### Phase 3 — Prepare for a small client pilot

Polish mobile layouts, add the minimal API, automated tests, useful error messages, deployment configuration, and operational documentation.

**Done when:** Permission, generation-failure rollback, input-validation, publishing, result-entry, and API-contract tests pass. A staging deployment supports the full workflow with synthetic users. HTTPS, password reset delivery, backups, and a documented restore/rollback process are configured before real-client launch. Production settings disable debug mode and keep credentials out of source control and logs.

### Phase 4 — Expand from actual client feedback

Add weekly check-ins, progress summaries, strength programming workflows, notifications, and business administration according to observed needs. Keep these out of the first release unless essential to a real client workflow.

## 9. Later enhancements — not first-release commitments

- Workout CSV ingestion with field/unit validation, duplicate detection, and rejected-record reporting.
- Monitoring of ingestion failures, missing values, and shifts in incoming data distributions.
- Managed object storage for uploaded files once file ingestion is introduced.
- Garmin/Strava integrations after verifying access requirements and deciding they are needed.
- Payments/subscriptions and any synchronization with Wix.
- Messaging, automated reminders, and richer progress visualizations.
- Multiple coaches, native mobile apps, advanced frontend frameworks, and infrastructure scaling.
- AI/ML features only when there is a defined use case and appropriate data. The generator does not need to be an ML model to support this business.

## 10. Deliverables expected from the implementing agent

- Working application source, migrations, and a reproducible local setup.
- README with setup, tests, generator integration, architecture, and deployment instructions.
- `.env.example` with placeholders only, plus synthetic demo data.
- Automated tests for the core workflow and authorization boundaries.
- Short API documentation and production readiness notes.
- A progress summary distinguishing completed features, mocked features, missing inputs, and remaining launch work.

Begin with repository/source inspection and Phase 1, then implement one complete coach-to-client workflow before broadening scope. This brief authorizes development planning and implementation within the receiving agent's granted workspace; it does not itself establish hosting credentials, a domain, spending approval, or permission to alter a live Wix site.

## Reference documentation

- Django: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- Wix backend environment: https://dev.wix.com/docs/develop-websites/articles/coding-with-velo/backend-code/about-the-site-backend
- Wix external subdomains: https://support.wix.com/en/article/connecting-a-subdomain-to-an-external-resource

Verify current deployment and framework documentation when implementing. No application code or production deployment is included with this brief.
