"""Publishing a draft: it becomes the client's live plan; the old live plan is archived (runs kept), all at once."""

from datetime import date, timedelta
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import ClientProfile, User
from training.models import PlanWeek, ScheduledWorkout, TrainingPlan, WorkoutResult

MONDAY = date(2026, 11, 23)


def make(profile, coach, status, title, kind="easy", prescription="Easy 5"):
    p = TrainingPlan.objects.create(
        client=profile, title=title, plan_type="half_marathon", status=status, created_by=coach,
        start_date=MONDAY, end_date=MONDAY + timedelta(days=6),
        published_at=timezone.now() if status != "draft" else None,
    )
    week = PlanWeek.objects.create(plan=p, number=1, start_date=MONDAY)
    ScheduledWorkout.objects.create(week=week, date=MONDAY, workout_type=kind, title=f"{title} Run",
                                    prescription=prescription)
    return p


class PublishTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.coach = User.objects.create_user("coach", password="x-Kairos-1234", role="coach")
        cls.other = User.objects.create_user("other", password="x-Kairos-1234", role="coach")
        cls.runner = User.objects.create_user("runner", password="x-Kairos-1234", role="client")
        cls.profile = ClientProfile.objects.create(user=cls.runner, coach=cls.coach)
        cls.old = make(cls.profile, cls.coach, "published", "Old Block")
        cls.draft = make(cls.profile, cls.coach, "draft", "New Block")
        WorkoutResult.objects.create(workout=ScheduledWorkout.objects.get(week__plan=cls.old), status="completed")

    def url(self, plan=None):
        return reverse("plan_publish", args=[(plan or self.draft).pk])

    def test_confirmation_page_explains_and_changes_nothing(self):
        self.client.force_login(self.coach)
        page = self.client.get(self.url())
        self.assertContains(page, "Publish This Plan?")
        self.assertContains(page, "Old Block")  # what it replaces
        self.assertContains(page, "moves to Past Plans")
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.status, "draft")

    def test_publish_swaps_the_live_plan_and_keeps_history(self):
        self.client.force_login(self.coach)
        r = self.client.post(self.url())
        self.assertRedirects(r, reverse("plan_detail", args=[self.draft.pk]))
        self.draft.refresh_from_db(); self.old.refresh_from_db()
        self.assertEqual(self.draft.status, "published")
        self.assertIsNotNone(self.draft.published_at)
        self.assertEqual(self.old.status, "archived")
        self.assertTrue(WorkoutResult.objects.filter(workout__week__plan=self.old).exists())
        # the client now sees the new plan as live and the old one under Past Plans
        self.client.force_login(self.runner)
        with mock.patch("training.views.client_today", return_value=MONDAY):
            home = self.client.get(reverse("client_home"))
        self.assertEqual(home.context["current"], self.draft)
        self.assertIn(self.old, list(home.context["past_plans"]))

    def test_first_plan_for_a_client(self):
        fresh = User.objects.create_user("fresh", password="x-Kairos-1234", role="client")
        profile = ClientProfile.objects.create(user=fresh, coach=self.coach)
        first = make(profile, self.coach, "draft", "First Block")
        self.client.force_login(self.coach)
        self.assertContains(self.client.get(self.url(first)), "nothing is replaced")
        self.client.post(self.url(first))
        first.refresh_from_db()
        self.assertEqual(first.status, "published")

    def test_unwritten_speed_sessions_are_flagged_but_allowed(self):
        draft = make(self.profile, self.coach, "draft", "Speedy", kind="threshold", prescription="")
        self.client.force_login(self.coach)
        page = self.client.get(self.url(draft))
        self.assertContains(page, "1 speed session not written yet")
        self.assertContains(page, "Publish Anyway")
        self.client.post(self.url(draft))
        draft.refresh_from_db()
        self.assertEqual(draft.status, "published")

    def test_only_drafts_and_never_from_the_trash(self):
        self.client.force_login(self.coach)
        self.client.post(self.url(self.old))  # already live
        self.old.refresh_from_db()
        self.assertEqual(self.old.status, "published")
        TrainingPlan.objects.filter(pk=self.draft.pk).update(trashed_at=timezone.now())
        self.assertEqual(self.client.post(self.url()).status_code, 404)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.status, "draft")

    def test_failure_leaves_both_plans_as_they_were(self):
        self.client.force_login(self.coach)
        real_save = TrainingPlan.save

        def boom(plan, *args, **kwargs):
            if plan.pk == self.draft.pk:
                raise RuntimeError("database hiccup")
            return real_save(plan, *args, **kwargs)

        with mock.patch.object(TrainingPlan, "save", boom), self.assertRaises(RuntimeError):
            self.client.post(self.url())
        self.old.refresh_from_db(); self.draft.refresh_from_db()
        self.assertEqual((self.old.status, self.draft.status), ("published", "draft"))

    def test_who_can_publish(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(self.url()).status_code, 404)
        self.client.force_login(self.runner)
        self.assertEqual(self.client.post(self.url()).status_code, 403)  # coach-only page, like every coach action
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.status, "draft")

    def test_publish_button_only_on_drafts(self):
        self.client.force_login(self.coach)
        self.assertContains(self.client.get(reverse("plan_detail", args=[self.draft.pk])), "Publish Plan")
        self.assertNotContains(self.client.get(reverse("plan_detail", args=[self.old.pk])), "Publish Plan")
