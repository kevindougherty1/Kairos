"""
Isolation and integrity tests (Phase 1 done-check: "one client cannot access the other's data").
Every cross-account request must look like "not found" (404), never leak data.
"""

from datetime import date, timedelta
from io import StringIO

from django.core import mail
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import ClientProfile, User
from core.units import format_distance, format_duration, miles_to_m
from training.models import PlanWeek, ScheduledWorkout, TrainingPlan, WorkoutResult

PASSWORD = "test-pass-Kairos-123"
MONDAY = date(2026, 11, 23)


def make_user(username, role, **extra):
    return User.objects.create_user(username, f"{username}@example.com", PASSWORD, role=role, **extra)


def make_plan(profile, coach, status, title="Plan"):
    plan = TrainingPlan.objects.create(
        client=profile, title=title, plan_type="half_marathon", status=status,
        start_date=MONDAY, end_date=MONDAY + timedelta(days=6), created_by=coach,
        published_at=timezone.now() if status != TrainingPlan.Status.DRAFT else None,
    )
    week = PlanWeek.objects.create(plan=plan, number=1, start_date=MONDAY, phase="Base")
    ScheduledWorkout.objects.create(week=week, date=MONDAY, workout_type="easy", title="Easy Run",
                                    target_distance_m=miles_to_m(5))
    return plan


def first_workout(plan):
    return ScheduledWorkout.objects.get(week__plan=plan)


class IsolationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.coach = make_user("coach", User.Role.COACH)
        cls.other_coach = make_user("other_coach", User.Role.COACH)
        cls.a = make_user("client_a", User.Role.CLIENT)
        cls.b = make_user("client_b", User.Role.CLIENT)
        cls.c = make_user("client_c", User.Role.CLIENT)  # belongs to the other coach
        cls.pa = ClientProfile.objects.create(user=cls.a, coach=cls.coach)
        cls.pb = ClientProfile.objects.create(user=cls.b, coach=cls.coach)
        cls.pc = ClientProfile.objects.create(user=cls.c, coach=cls.other_coach)

        cls.a_live = make_plan(cls.pa, cls.coach, TrainingPlan.Status.PUBLISHED, "A Live")
        cls.a_draft = make_plan(cls.pa, cls.coach, TrainingPlan.Status.DRAFT, "A Draft")
        cls.b_live = make_plan(cls.pb, cls.coach, TrainingPlan.Status.PUBLISHED, "B Live")
        cls.c_live = make_plan(cls.pc, cls.other_coach, TrainingPlan.Status.PUBLISHED, "C Live")

    def login(self, user):
        self.client.force_login(user)

    def get(self, name, pk):
        return self.client.get(reverse(name, args=[pk]))

    # Anonymous
    def test_anonymous_is_sent_to_login(self):
        for url in [reverse("dashboard"), reverse("plan_detail", args=[self.a_live.pk]),
                    reverse("workout_detail", args=[first_workout(self.a_live).pk])]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, url)
            self.assertTrue(response.url.startswith(reverse("login")), url)

    # Client sees own published data
    def test_client_sees_own_published_plan_and_workout(self):
        self.login(self.a)
        self.assertEqual(self.get("plan_detail", self.a_live.pk).status_code, 200)
        self.assertEqual(self.get("workout_detail", first_workout(self.a_live).pk).status_code, 200)

    def test_client_home_lists_only_own_live_plan(self):
        self.login(self.a)
        response = self.client.get(reverse("client_home"))
        self.assertContains(response, "A Live")
        for hidden in ("A Draft", "B Live", "C Live"):
            self.assertNotContains(response, hidden)

    # Client can't see drafts
    def test_client_cannot_see_own_draft(self):
        self.login(self.a)
        self.assertEqual(self.get("plan_detail", self.a_draft.pk).status_code, 404)
        self.assertEqual(self.get("workout_detail", first_workout(self.a_draft).pk).status_code, 404)

    # Client can't see other clients
    def test_client_cannot_read_other_clients_plan_or_workout(self):
        self.login(self.a)
        for plan in (self.b_live, self.c_live):
            self.assertEqual(self.get("plan_detail", plan.pk).status_code, 404)
            self.assertEqual(self.get("workout_detail", first_workout(plan).pk).status_code, 404)

    def test_client_cannot_write_result_to_other_clients_workout(self):
        self.login(self.a)
        response = self.client.post(reverse("workout_detail", args=[first_workout(self.b_live).pk]),
                                    {"status": "completed"})
        self.assertEqual(response.status_code, 404)
        self.assertFalse(WorkoutResult.objects.exists())

    def test_client_cannot_open_coach_pages(self):
        self.login(self.a)
        self.assertEqual(self.client.get(reverse("coach_home")).status_code, 403)

    # Coach scope
    def test_coach_sees_only_own_clients(self):
        self.login(self.coach)
        response = self.client.get(reverse("coach_home"))
        self.assertContains(response, "client_a")
        self.assertContains(response, "client_b")
        self.assertNotContains(response, "client_c")
        self.assertEqual(self.get("plan_detail", self.c_live.pk).status_code, 404)
        self.assertEqual(self.get("workout_detail", first_workout(self.c_live).pk).status_code, 404)

    def test_coach_can_review_own_clients_draft(self):
        self.login(self.coach)
        self.assertEqual(self.get("plan_detail", self.a_draft.pk).status_code, 200)

    def test_coach_cannot_log_results_for_a_client(self):
        self.login(self.coach)
        response = self.client.post(reverse("workout_detail", args=[first_workout(self.a_live).pk]),
                                    {"status": "completed"})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(WorkoutResult.objects.exists())

    def test_coach_cannot_open_client_home(self):
        self.login(self.coach)
        self.assertEqual(self.client.get(reverse("client_home")).status_code, 403)

    # Result entry
    def test_resubmitting_a_result_updates_instead_of_duplicating(self):
        self.login(self.a)
        url = reverse("workout_detail", args=[first_workout(self.a_live).pk])
        self.client.post(url, {"status": "partial", "distance": "3.5", "duration": "35:00", "perceived_effort": "4"})
        self.client.post(url, {"status": "completed", "distance": "5", "duration": "48:30", "perceived_effort": "5"})
        self.assertEqual(WorkoutResult.objects.count(), 1)
        result = WorkoutResult.objects.get()
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.actual_distance_m, miles_to_m(5))
        self.assertEqual(result.actual_duration_s, 48 * 60 + 30)

    def test_submitted_ownership_fields_are_ignored(self):
        self.login(self.a)
        own = first_workout(self.a_live)
        self.client.post(reverse("workout_detail", args=[own.pk]), {
            "status": "completed", "workout": first_workout(self.b_live).pk, "prescription_version": 99,
        })
        result = WorkoutResult.objects.get()
        self.assertEqual(result.workout, own)
        self.assertEqual(result.prescription_version, own.version)

    def test_client_cannot_log_results_on_archived_plan(self):
        archived = make_plan(self.pa, self.coach, TrainingPlan.Status.ARCHIVED, "A Old")
        self.login(self.a)
        url = reverse("workout_detail", args=[first_workout(archived).pk])
        self.assertEqual(self.client.get(url).status_code, 200)  # can still read it
        self.assertEqual(self.client.post(url, {"status": "completed"}).status_code, 403)

    def test_invalid_effort_is_rejected(self):
        self.login(self.a)
        url = reverse("workout_detail", args=[first_workout(self.a_live).pk])
        response = self.client.post(url, {"status": "completed", "perceived_effort": "11"})
        self.assertEqual(response.status_code, 200)  # form re-rendered with an error
        self.assertFalse(WorkoutResult.objects.exists())

    # Login flow
    def test_login_redirects_by_role(self):
        response = self.client.post(reverse("login"), {"username": "coach", "password": PASSWORD}, follow=True)
        self.assertEqual(response.redirect_chain[-1][0], reverse("coach_home"))
        self.client.logout()
        response = self.client.post(reverse("login"), {"username": "client_a", "password": PASSWORD}, follow=True)
        self.assertEqual(response.redirect_chain[-1][0], reverse("client_home"))

    def test_inactive_user_cannot_log_in(self):
        self.b.is_active = False
        self.b.save()
        response = self.client.post(reverse("login"), {"username": "client_b", "password": PASSWORD})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_requires_post_and_ends_session(self):
        self.login(self.a)
        self.client.post(reverse("logout"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_password_reset_sends_email(self):
        response = self.client.post(reverse("password_reset"), {"email": "client_a@example.com"})
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("client_a", mail.outbox[0].body)


class ConstraintTests(TestCase):
    """The database itself refuses bad data, even if a view or admin form missed it."""

    @classmethod
    def setUpTestData(cls):
        cls.coach = make_user("coach", User.Role.COACH)
        cls.profile = ClientProfile.objects.create(user=make_user("client", User.Role.CLIENT), coach=cls.coach)
        cls.live = make_plan(cls.profile, cls.coach, TrainingPlan.Status.PUBLISHED)

    def assertRejected(self, func):
        with self.assertRaises(IntegrityError), transaction.atomic():
            func()

    def test_one_published_plan_per_client(self):
        self.assertRejected(lambda: make_plan(self.profile, self.coach, TrainingPlan.Status.PUBLISHED))

    def test_one_result_per_workout(self):
        workout = first_workout(self.live)
        WorkoutResult.objects.create(workout=workout, status="completed")
        self.assertRejected(lambda: WorkoutResult.objects.create(workout=workout, status="skipped"))

    def test_effort_must_be_1_to_10(self):
        self.assertRejected(lambda: WorkoutResult.objects.create(
            workout=first_workout(self.live), status="completed", perceived_effort=11))

    def test_plan_end_not_before_start(self):
        self.assertRejected(lambda: TrainingPlan.objects.create(
            client=self.profile, title="Bad", plan_type="marathon", start_date=MONDAY,
            end_date=MONDAY - timedelta(days=1), created_by=self.coach))

    def test_results_protect_workouts_from_deletion(self):
        from django.db.models import ProtectedError

        WorkoutResult.objects.create(workout=first_workout(self.live), status="completed")
        with self.assertRaises(ProtectedError):
            first_workout(self.live).delete()

    def test_superuser_defaults_to_coach(self):
        admin = User.objects.create_superuser("boss", "boss@example.com", PASSWORD)
        self.assertEqual(admin.role, User.Role.COACH)

    def test_new_user_defaults_to_client(self):
        self.assertEqual(User.objects.create_user("new", password=PASSWORD).role, User.Role.CLIENT)


class UnitTests(TestCase):
    def test_distance_formatting(self):
        self.assertEqual(format_distance(21098, "mi"), "13.1 mi")
        self.assertEqual(format_distance(42195, "km"), "42.2 km")
        self.assertEqual(format_distance(miles_to_m(6), "mi"), "6 mi")

    def test_duration_formatting(self):
        self.assertEqual(format_duration(2700), "45:00")
        self.assertEqual(format_duration(3930), "1:05:30")


@override_settings(DEBUG=True)
class SeedDemoTests(TestCase):
    def test_seed_demo_creates_labeled_fixtures_and_is_rerunnable(self):
        call_command("seed_demo", password=PASSWORD, stdout=StringIO())
        call_command("seed_demo", password=PASSWORD, stdout=StringIO())  # re-run must not duplicate
        self.assertEqual(User.objects.filter(username__startswith="demo_").count(), 3)
        self.assertTrue(TrainingPlan.objects.exists())
        self.assertFalse(TrainingPlan.objects.filter(is_fixture=False).exists())
        self.assertEqual(TrainingPlan.objects.filter(status="published").count(), 2)
        self.assertEqual(TrainingPlan.objects.filter(status="draft").count(), 1)

    @override_settings(DEBUG=False)
    def test_seed_demo_refuses_without_debug(self):
        from django.core.management.base import CommandError

        with self.assertRaises(CommandError):
            call_command("seed_demo", stdout=StringIO())
