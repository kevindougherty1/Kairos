"""Clients see "Speed Session" + only what the coach wrote; the engine's pick is a coach-only suggestion.
Edits to a live plan keep the old version (brief §6)."""

from datetime import date
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import ClientProfile, User
from core.units import miles_to_m
from training.engines import PlanRequest
from training.models import PrescriptionRevision, ScheduledWorkout, TrainingPlan, WorkoutResult
from training.services import generate_draft

TODAY = date(2026, 11, 25)


class PrescribeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.coach = User.objects.create_user("coach", password="x-Kairos-1234", role="coach")
        cls.other = User.objects.create_user("other", password="x-Kairos-1234", role="coach")
        cls.runner = User.objects.create_user("runner", password="x-Kairos-1234", role="client")
        cls.profile = ClientProfile.objects.create(user=cls.runner, coach=cls.coach)
        req = PlanRequest(plan_type="half_marathon", experience="intermediate", current_mileage=30, longest_run=10,
                          runs_per_week=5, weeks=12, race_date=date(2027, 3, 14), race_name="Spring Half")
        cls.plan = generate_draft(cls.coach, cls.profile, req, today=TODAY)
        cls.speed = ScheduledWorkout.objects.filter(week__plan=cls.plan, workout_type="threshold").order_by("date").first()

    def publish(self):
        TrainingPlan.objects.filter(pk=self.plan.pk).update(status="published", published_at=timezone.now())

    def page(self, user, workout=None, **params):
        self.client.force_login(user)
        return self.client.get(reverse("workout_detail", args=[(workout or self.speed).pk]), params)

    def prescribe(self, user, **data):
        self.client.force_login(user)
        payload = {"title": "Speed Session", "distance": "5", "prescription": "", "coach_notes": ""}
        payload.update(data)
        return self.client.post(reverse("workout_prescribe", args=[self.speed.pk]), payload)

    def test_client_sees_speed_session_and_nothing_from_the_engine(self):
        self.publish()
        r = self.page(self.runner)
        self.assertContains(r, "Speed Session")
        self.assertContains(r, "Your coach will add the details for this session.")
        for hidden in ("Threshold", "Cruise", "Tempo", "Suggested style", "Engine Suggestion", self.speed.suggestion[:30]):
            self.assertNotContains(r, hidden)

    def test_coach_sees_the_engine_pick_as_a_suggestion(self):
        r = self.page(self.coach)
        self.assertContains(r, "Engine Suggestion")
        self.assertContains(r, "Only you see this")
        self.assertContains(r, self.speed.engine_detail)
        self.assertContains(r, "Not written yet")
        self.assertContains(r, "Start From the Suggestion")

    def test_start_from_suggestion_prefills_but_saves_nothing(self):
        r = self.page(self.coach, use_suggestion="1")
        self.assertEqual(r.context["prescription_form"].initial["prescription"], self.speed.suggestion)
        self.speed.refresh_from_db()
        self.assertEqual(self.speed.prescription, "")

    def test_editing_a_draft_saves_without_versions(self):
        self.prescribe(self.coach, prescription="2 mi easy, 3 x 1 mi at threshold, 1 mi easy", distance="5")
        self.speed.refresh_from_db()
        self.assertEqual(self.speed.prescription, "2 mi easy, 3 x 1 mi at threshold, 1 mi easy")
        self.assertEqual(self.speed.target_distance_m, miles_to_m(5))
        self.assertEqual(self.speed.version, 1)
        self.assertFalse(PrescriptionRevision.objects.exists())

    def test_editing_a_live_plan_keeps_the_old_version(self):
        self.publish()
        self.prescribe(self.coach, prescription="4 x 1 mi at threshold")
        WorkoutResult.objects.create(workout=self.speed, status="completed", prescription_version=2)
        self.prescribe(self.coach, prescription="5 x 1 mi at threshold")
        self.speed.refresh_from_db()
        self.assertEqual(self.speed.version, 3)
        old = PrescriptionRevision.objects.get(workout=self.speed, version=2)
        self.assertEqual(old.snapshot["prescription"], "4 x 1 mi at threshold")
        self.assertEqual(old.changed_by, self.coach)
        r = self.page(self.runner)
        self.assertContains(r, "5 x 1 mi at threshold")
        self.assertContains(r, "Your coach updated this workout after you logged it.")

    def test_saving_without_changes_creates_no_version(self):
        self.publish()
        self.prescribe(self.coach, prescription="Same")
        self.prescribe(self.coach, prescription="Same")
        self.speed.refresh_from_db()
        self.assertEqual(self.speed.version, 2)
        self.assertEqual(PrescriptionRevision.objects.count(), 1)

    def test_who_can_prescribe(self):
        self.assertEqual(self.prescribe(self.runner, prescription="x").status_code, 403)
        self.assertEqual(self.prescribe(self.other, prescription="x").status_code, 404)
        self.client.force_login(self.coach)
        self.assertEqual(self.client.get(reverse("workout_prescribe", args=[self.speed.pk])).status_code, 405)
        TrainingPlan.objects.filter(pk=self.plan.pk).update(status="archived", published_at=timezone.now())
        self.assertEqual(self.prescribe(self.coach, prescription="x").status_code, 403)
        self.speed.refresh_from_db()
        self.assertEqual(self.speed.prescription, "")

    def test_plan_page_counts_sessions_to_write_for_the_coach_only(self):
        self.client.force_login(self.coach)
        r = self.client.get(reverse("plan_detail", args=[self.plan.pk]))
        self.assertContains(r, "speed sessions to write")
        self.assertContains(r, "To Write")
        self.publish()
        self.client.force_login(self.runner)
        r = self.client.get(reverse("plan_detail", args=[self.plan.pk]))
        self.assertNotContains(r, "To Write")
        self.assertNotContains(r, "Threshold")
