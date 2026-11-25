"""Coach feedback on logged runs: only the client's coach writes it; the client sees it, with a New badge until opened."""

from datetime import date, timedelta
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import ClientProfile, User
from training.models import PlanWeek, ScheduledWorkout, TrainingPlan, WorkoutResult

MONDAY = date(2026, 11, 23)


class FeedbackTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.coach = User.objects.create_user("coach", password="x-Kairos-1234", role="coach")
        cls.other = User.objects.create_user("other", password="x-Kairos-1234", role="coach")
        cls.runner = User.objects.create_user("runner", password="x-Kairos-1234", role="client")
        cls.other_runner = User.objects.create_user("stranger", password="x-Kairos-1234", role="client")
        cls.profile = ClientProfile.objects.create(user=cls.runner, coach=cls.coach)
        cls.other_profile = ClientProfile.objects.create(user=cls.other_runner, coach=cls.other)
        cls.plan = TrainingPlan.objects.create(
            client=cls.profile, title="Live", plan_type="half_marathon", status="published", published_at=timezone.now(),
            start_date=MONDAY, end_date=MONDAY + timedelta(days=6), created_by=cls.coach,
        )
        week = PlanWeek.objects.create(plan=cls.plan, number=1, start_date=MONDAY)
        cls.logged_run = ScheduledWorkout.objects.create(week=week, date=MONDAY, workout_type="easy", title="Easy Run")
        cls.unlogged = ScheduledWorkout.objects.create(week=week, date=MONDAY + timedelta(days=2), workout_type="easy",
                                                       title="Easy Run")
        cls.result = WorkoutResult.objects.create(workout=cls.logged_run, status="completed", perceived_effort=4,
                                                  comments="Legs felt heavy")
        other_plan = TrainingPlan.objects.create(
            client=cls.other_profile, title="Theirs", plan_type="half_marathon", status="published",
            published_at=timezone.now(), start_date=MONDAY, end_date=MONDAY + timedelta(days=6), created_by=cls.other,
        )
        ow = PlanWeek.objects.create(plan=other_plan, number=1, start_date=MONDAY)
        cls.other_run = ScheduledWorkout.objects.create(week=ow, date=MONDAY, workout_type="easy", title="Secret Run")
        WorkoutResult.objects.create(workout=cls.other_run, status="completed", comments="Stranger comment")

    def send(self, user, workout=None, text="Nice and steady. Keep the next one easy too."):
        self.client.force_login(user)
        return self.client.post(reverse("result_feedback", args=[(workout or self.logged_run).pk]), {"feedback": text})

    def test_coach_sends_feedback_and_client_sees_it(self):
        logged_at = self.result.updated_at
        self.send(self.coach)
        self.result.refresh_from_db()
        self.assertEqual(self.result.updated_at, logged_at)  # the client's "Logged" time doesn't move
        self.assertEqual(self.result.coach_feedback, "Nice and steady. Keep the next one easy too.")
        self.assertIsNotNone(self.result.coach_feedback_at)
        self.client.force_login(self.runner)
        page = self.client.get(reverse("workout_detail", args=[self.logged_run.pk]))
        self.assertContains(page, "Coach Feedback")
        self.assertContains(page, "Nice and steady.")

    def test_new_feedback_badge_until_the_client_opens_the_run(self):
        self.send(self.coach)
        self.client.force_login(self.runner)
        with mock.patch("training.views.client_today", return_value=MONDAY):
            self.assertContains(self.client.get(reverse("client_home")), "New Feedback")
            self.client.get(reverse("workout_detail", args=[self.logged_run.pk]))  # opening it marks it seen
            self.assertNotContains(self.client.get(reverse("client_home")), "New Feedback")
        self.client.force_login(self.coach)
        self.assertContains(self.client.get(reverse("workout_detail", args=[self.logged_run.pk])), "Seen by your client")

    def test_updated_feedback_is_new_again(self):
        self.send(self.coach)
        self.client.force_login(self.runner)
        self.client.get(reverse("workout_detail", args=[self.logged_run.pk]))
        self.send(self.coach, text="One more thing: hydrate.")
        self.result.refresh_from_db()
        self.assertTrue(self.result.has_new_feedback)

    def test_empty_feedback_removes_it(self):
        self.send(self.coach)
        self.send(self.coach, text="   ")
        self.result.refresh_from_db()
        self.assertEqual(self.result.coach_feedback, "")
        self.assertIsNone(self.result.coach_feedback_at)

    def test_client_cannot_write_feedback_even_through_their_result_form(self):
        self.assertEqual(self.send(self.runner).status_code, 403)
        self.client.force_login(self.runner)
        self.client.post(reverse("workout_detail", args=[self.logged_run.pk]),
                         {"status": "completed", "coach_feedback": "I'm great, says coach"})
        self.result.refresh_from_db()
        self.assertEqual(self.result.coach_feedback, "")

    def test_other_coach_and_unlogged_runs_are_refused(self):
        self.assertEqual(self.send(self.other).status_code, 404)
        self.assertEqual(self.send(self.coach, workout=self.other_run).status_code, 404)
        self.assertEqual(self.send(self.coach, workout=self.unlogged).status_code, 404)  # nothing to reply to
        self.client.force_login(self.coach)
        self.assertEqual(self.client.get(reverse("result_feedback", args=[self.logged_run.pk])).status_code, 405)

    def test_runs_to_review_on_the_coach_home(self):
        self.client.force_login(self.coach)
        home = self.client.get(reverse("coach_home"))
        self.assertContains(home, "Runs to Review")
        self.assertContains(home, "Legs felt heavy")
        self.assertContains(home, ">Reply<")
        self.assertNotContains(home, "Stranger comment")  # another coach's client
        self.send(self.coach)
        self.assertContains(self.client.get(reverse("coach_home")), ">Replied<")
