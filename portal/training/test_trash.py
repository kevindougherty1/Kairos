"""Trash: hide dead plans, restore them, delete forever, without ever losing the live plan or client history."""

from datetime import date, timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import ClientProfile, User
from training.models import PlanWeek, ScheduledWorkout, TrainingPlan, WorkoutResult

MONDAY = date(2026, 11, 23)


def plan(profile, coach, status, title):
    p = TrainingPlan.objects.create(
        client=profile, title=title, plan_type="half_marathon", status=status, created_by=coach,
        start_date=MONDAY, end_date=MONDAY + timedelta(days=6),
        published_at=timezone.now() if status != "draft" else None,
    )
    week = PlanWeek.objects.create(plan=p, number=1, start_date=MONDAY)
    ScheduledWorkout.objects.create(week=week, date=MONDAY, workout_type="easy", title=f"{title} Run")
    return p


class TrashTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.coach = User.objects.create_user("coach", password="x-Kairos-1234", role="coach")
        cls.other = User.objects.create_user("other", password="x-Kairos-1234", role="coach")
        cls.runner = User.objects.create_user("runner", password="x-Kairos-1234", role="client")
        cls.profile = ClientProfile.objects.create(user=cls.runner, coach=cls.coach)
        cls.live = plan(cls.profile, cls.coach, "published", "Live Plan")
        cls.draft = plan(cls.profile, cls.coach, "draft", "Dead Draft")
        cls.old = plan(cls.profile, cls.coach, "archived", "Old Plan")

    def post(self, user, name, p, **data):
        self.client.force_login(user)
        return self.client.post(reverse(name, args=[p.pk]), data)

    def test_trash_hides_a_draft_from_the_coach_list_and_shows_it_in_trash(self):
        r = self.post(self.coach, "plan_trash", self.draft, next=reverse("coach_home"))
        self.assertRedirects(r, reverse("coach_home"))
        self.draft.refresh_from_db()
        self.assertIsNotNone(self.draft.trashed_at)
        self.assertEqual(self.draft.trashed_by, self.coach)
        home = self.client.get(reverse("coach_home"))
        self.assertNotContains(home, "Dead Draft Run")
        self.assertContains(home, 'aria-label="1 plan"')
        self.assertContains(self.client.get(reverse("coach_trash")), "Dead Draft")
        self.assertEqual(self.client.get(reverse("plan_detail", args=[self.draft.pk])).status_code, 404)

    def test_undo_message_and_restore(self):
        self.post(self.coach, "plan_trash", self.draft)
        home = self.client.get(reverse("coach_home"))
        self.assertContains(home, reverse("plan_restore", args=[self.draft.pk]))  # the Undo button
        self.post(self.coach, "plan_restore", self.draft)
        self.draft.refresh_from_db()
        self.assertIsNone(self.draft.trashed_at)
        self.assertEqual(self.client.get(reverse("plan_detail", args=[self.draft.pk])).status_code, 200)

    def test_live_plan_cannot_be_trashed(self):
        r = self.post(self.coach, "plan_trash", self.live)
        self.assertRedirects(r, reverse("plan_detail", args=[self.live.pk]))
        self.live.refresh_from_db()
        self.assertIsNone(self.live.trashed_at)
        with self.assertRaises(IntegrityError), transaction.atomic():  # the database refuses it too
            TrainingPlan.objects.filter(pk=self.live.pk).update(trashed_at=timezone.now())

    def test_trashed_archived_plan_disappears_for_the_client_but_results_stay(self):
        workout = ScheduledWorkout.objects.get(week__plan=self.old)
        WorkoutResult.objects.create(workout=workout, status="completed")
        self.client.force_login(self.runner)
        self.assertEqual(self.client.get(reverse("plan_detail", args=[self.old.pk])).status_code, 200)
        self.post(self.coach, "plan_trash", self.old)
        self.client.force_login(self.runner)
        self.assertEqual(self.client.get(reverse("plan_detail", args=[self.old.pk])).status_code, 404)
        self.assertTrue(WorkoutResult.objects.filter(workout=workout).exists())

    def test_delete_forever_needs_trash_then_confirmation(self):
        self.client.force_login(self.coach)
        self.assertEqual(self.client.get(reverse("plan_delete", args=[self.draft.pk])).status_code, 404)  # not in trash
        self.post(self.coach, "plan_trash", self.draft)
        confirm = self.client.get(reverse("plan_delete", args=[self.draft.pk]))
        self.assertContains(confirm, "can’t be undone")
        self.assertTrue(TrainingPlan.objects.filter(pk=self.draft.pk).exists())  # GET deletes nothing
        self.post(self.coach, "plan_delete", self.draft)
        self.assertFalse(TrainingPlan.objects.filter(pk=self.draft.pk).exists())
        self.assertFalse(ScheduledWorkout.objects.filter(title="Dead Draft Run").exists())

    def test_plan_with_logged_runs_is_never_deleted_forever(self):
        WorkoutResult.objects.create(workout=ScheduledWorkout.objects.get(week__plan=self.old), status="completed")
        self.post(self.coach, "plan_trash", self.old)
        self.assertContains(self.client.get(reverse("plan_delete", args=[self.old.pk])), "1 logged run")
        self.post(self.coach, "plan_delete", self.old)
        self.assertTrue(TrainingPlan.objects.filter(pk=self.old.pk).exists())

    def test_only_the_own_coach_and_only_by_post(self):
        self.client.force_login(self.coach)
        self.assertEqual(self.client.get(reverse("plan_trash", args=[self.draft.pk])).status_code, 405)
        self.assertEqual(self.post(self.other, "plan_trash", self.draft).status_code, 404)
        self.assertEqual(self.post(self.runner, "plan_trash", self.draft).status_code, 403)
        self.post(self.coach, "plan_trash", self.draft)
        self.client.get(reverse("coach_home"))  # the coach sees (and so clears) their "Moved to Trash" notice
        self.assertEqual(self.post(self.other, "plan_restore", self.draft).status_code, 404)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse("plan_delete", args=[self.draft.pk])).status_code, 404)
        self.assertNotContains(self.client.get(reverse("coach_trash")), "Dead Draft")

    def test_next_parameter_cannot_redirect_off_site(self):
        r = self.post(self.coach, "plan_trash", self.draft, next="https://evil.example/")
        self.assertRedirects(r, reverse("coach_home"))
