"""Engine snapshots, the HM adapter, and draft generation (Phase 2 start)."""

from datetime import date, timedelta
from unittest import mock

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from accounts.models import ClientProfile, RaceDistance, User
from core.units import miles_to_m
from training import golden
from training.engines import PlanRequest, generate_half_marathon, generator_version
from training.models import PlanWeek, ScheduledWorkout, TrainingPlan, WorkoutResult
from training.services import generate_draft

RACE_SAT = date(2027, 3, 13)   # a Saturday
RACE_SUN = date(2027, 3, 14)   # a Sunday
TODAY = date(2026, 11, 25)


def hm_request(**overrides):
    data = dict(plan_type="half_marathon", experience="intermediate", current_mileage=25, longest_run=8,
                runs_per_week=5, weeks=12, race_date=RACE_SAT, race_name="Spring Half",
                long_run_day="Sat", quality_day="Tue", unavailable_days=[], preferred_rest_days=["Sun"])
    data.update(overrides)
    return PlanRequest(**data)


class GoldenSnapshotTests(SimpleTestCase):
    """If an engine's output changes, these fail. Refresh with `manage.py engine_golden --update` only on purpose."""

    def check(self, name):
        import json

        expected = json.loads(golden.path(name).read_text(encoding="utf-8"))
        current = json.loads(golden.dump(golden.BUILDERS[name]()))
        self.assertEqual(sorted(current), sorted(expected), f"{name}: the case list changed")
        for case in expected:
            self.assertEqual(current[case], expected[case], f"{name} engine output changed for case {case}")

    def test_half_marathon_engine_matches_snapshot(self):
        self.check("hm")

    def test_marathon_engine_matches_snapshot(self):
        self.check("marathon")


class PlanRequestTests(SimpleTestCase):
    def assertInvalid(self, field, **overrides):
        with self.assertRaises(ValidationError) as ctx:
            hm_request(**overrides).validate(today=TODAY)
        self.assertIn(field, ctx.exception.message_dict)

    def test_valid_request_passes(self):
        hm_request().validate(today=TODAY)

    def test_plan_length_limits(self):
        self.assertInvalid("weeks", weeks=7)
        self.assertInvalid("weeks", weeks=21)
        hm_request(weeks=8).validate(today=TODAY)
        hm_request(weeks=20, race_date=date(2027, 6, 12)).validate(today=TODAY)  # 20 weeks needs a later race

    def test_engine_input_limits(self):
        self.assertInvalid("runs_per_week", runs_per_week=3)
        self.assertInvalid("runs_per_week", runs_per_week=7)
        self.assertInvalid("experience", experience="Beginner")
        self.assertInvalid("long_run_day", long_run_day="Saturday")
        self.assertInvalid("plan_type", plan_type="speed")

    def test_plan_cannot_start_in_the_past(self):
        # Race 4 weeks out: a 12-week plan would have started 8 weeks ago.
        self.assertInvalid("weeks", race_date=TODAY + timedelta(weeks=4), weeks=12)

    def test_dates_count_back_from_race_week(self):
        r = hm_request(weeks=12, race_date=RACE_SUN)
        self.assertEqual(r.end_date, date(2027, 3, 14))            # Sunday of race week
        self.assertEqual(r.start_date, date(2026, 12, 21))         # Monday, 11 weeks before race week
        self.assertEqual(r.start_date.weekday(), 0)

    def test_engine_kwargs_use_the_engines_own_names(self):
        kw = hm_request().to_engine_kwargs()
        self.assertEqual(kw["recent_longest_run"], 8)
        self.assertEqual(kw["preferences"]["quality_day"], "Tue")


class HalfMarathonAdapterTests(SimpleTestCase):
    def test_normalized_plan_shape(self):
        version, kwargs, plan = generate_half_marathon(hm_request())
        self.assertRegex(version, r"^half_marathon_engine_main_4plus_v5_7@[0-9a-f]{12}$")
        self.assertEqual(len(plan["weeks"]), 12)
        for wk in plan["weeks"]:
            self.assertEqual(wk["start_date"].weekday(), 0)
            for w in wk["workouts"]:
                self.assertTrue(wk["start_date"] <= w["date"] <= wk["start_date"] + timedelta(days=6))

    def test_weeks_match_the_engine_mileage_except_race_week(self):
        from half_marathon_engine_main_4plus_v5_7 import build_plan

        _, _, plan = generate_half_marathon(hm_request())
        _, engine = build_plan(**hm_request().to_engine_kwargs())
        for ours, theirs in zip(plan["weeks"][:-1], engine[:-1]):
            self.assertEqual(ours["target_distance_m"], miles_to_m(theirs["mileage"]))
            self.assertEqual(ours["phase"], theirs["phase"])

    def test_race_lands_on_the_real_race_date_with_race_distance(self):
        _, _, plan = generate_half_marathon(hm_request(race_date=RACE_SUN, long_run_day="Sat"))
        race_week = plan["weeks"][-1]
        races = [w for w in race_week["workouts"] if w["kind"] == "race"]
        self.assertEqual(len(races), 1)
        self.assertEqual(races[0]["date"], RACE_SUN)               # moved from the long-run day (Sat) to Sunday
        self.assertEqual(races[0]["distance_m"], RaceDistance.HALF_MARATHON)
        self.assertEqual(races[0]["title"], "Spring Half")
        shakeouts = sum(w["distance_m"] for w in race_week["workouts"] if w["kind"] == "shakeout")
        self.assertEqual(race_week["target_distance_m"], shakeouts + RaceDistance.HALF_MARATHON)

    def test_a_run_on_race_day_gives_way_to_the_race(self):
        # Long run Sat → engine shakeouts on Mon and Wed; a Wednesday race must replace the Wed shakeout.
        _, _, plan = generate_half_marathon(hm_request(race_date=date(2027, 3, 10), long_run_day="Sat"))
        race_week = plan["weeks"][-1]
        on_race_day = [w for w in race_week["workouts"] if w["date"] == date(2027, 3, 10)]
        self.assertEqual([w["kind"] for w in on_race_day], ["race"])
        self.assertTrue(any("race day" in m for m in race_week["warnings"]))

    def test_engine_guidance_is_a_coach_suggestion_not_the_prescription(self):
        _, _, plan = generate_half_marathon(hm_request())
        threshold = next(w for wk in plan["weeks"] for w in wk["workouts"] if w["kind"] == "threshold")
        self.assertEqual(threshold["title"], "Speed Session")
        self.assertEqual(threshold["prescription"], "")
        self.assertIn("Suggested style:", threshold["suggestion"])
        self.assertIn("Effort:", threshold["suggestion"])
        self.assertTrue(threshold["engine_detail"].startswith("Threshold · "))

    def test_client_facing_names(self):
        _, _, plan = generate_half_marathon(hm_request(runs_per_week=5))
        titles = {w["kind"]: w["title"] for wk in plan["weeks"] for w in wk["workouts"]}
        for kind in ("threshold", "race_pace", "hills", "speed"):
            if kind in titles:
                self.assertEqual(titles[kind], "Speed Session", kind)
        self.assertEqual(titles.get("economy"), "Easy Run + Strides")
        self.assertEqual(titles["easy"], "Easy Run")


class GenerateDraftTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.coach = User.objects.create_user("coach", password="x-Kairos-1234", role="coach")
        cls.other_coach = User.objects.create_user("other", password="x-Kairos-1234", role="coach")
        cls.client_user = User.objects.create_user("runner", password="x-Kairos-1234", role="client")
        cls.profile = ClientProfile.objects.create(user=cls.client_user, coach=cls.coach, experience="intermediate",
                                                   runs_per_week=5, target_race_name="Spring Half",
                                                   target_race_date=RACE_SAT)

    def test_saves_a_complete_draft_with_provenance(self):
        plan = generate_draft(self.coach, self.profile, hm_request(), today=TODAY)
        self.assertEqual(plan.status, TrainingPlan.Status.DRAFT)
        self.assertFalse(plan.is_fixture)
        self.assertEqual(plan.generator_version, generator_version("half_marathon_engine_main_4plus_v5_7.py"))
        self.assertEqual(plan.input_snapshot["request"]["weeks"], 12)
        self.assertEqual(plan.input_snapshot["engine_kwargs"]["recent_longest_run"], 8)
        self.assertEqual(plan.weeks.count(), 12)
        self.assertEqual(plan.race_distance_m, RaceDistance.HALF_MARATHON)
        self.assertTrue(ScheduledWorkout.objects.filter(week__plan=plan, workout_type="race", date=RACE_SAT).exists())
        self.assertEqual((plan.start_date, plan.end_date), (date(2026, 12, 21), date(2027, 3, 14)))

    def test_failure_midway_saves_nothing(self):
        real_create = ScheduledWorkout.objects.create
        calls = {"n": 0}

        def flaky(**kw):
            calls["n"] += 1
            if calls["n"] == 20:
                raise RuntimeError("disk full")
            return real_create(**kw)

        with mock.patch.object(ScheduledWorkout.objects, "create", side_effect=flaky):
            with self.assertRaises(RuntimeError):
                generate_draft(self.coach, self.profile, hm_request(), today=TODAY)
        self.assertFalse(TrainingPlan.objects.exists())
        self.assertFalse(PlanWeek.objects.exists())
        self.assertFalse(ScheduledWorkout.objects.exists())

    def test_existing_plans_and_results_are_untouched(self):
        first = generate_draft(self.coach, self.profile, hm_request(), today=TODAY)
        first.status, first.published_at = "published", first.created_at
        first.save()
        workout = ScheduledWorkout.objects.filter(week__plan=first).first()
        WorkoutResult.objects.create(workout=workout, status="completed")
        second = generate_draft(self.coach, self.profile, hm_request(current_mileage=30), today=TODAY)
        self.assertNotEqual(first.pk, second.pk)
        first.refresh_from_db()
        self.assertEqual(first.status, "published")
        self.assertEqual(WorkoutResult.objects.get().workout, workout)
        self.assertEqual(TrainingPlan.objects.count(), 2)

    def test_only_the_clients_own_coach_can_generate(self):
        with self.assertRaises(PermissionDenied):
            generate_draft(self.other_coach, self.profile, hm_request(), today=TODAY)
        with self.assertRaises(PermissionDenied):
            generate_draft(self.client_user, self.profile, hm_request(), today=TODAY)
        self.assertFalse(TrainingPlan.objects.exists())


class GeneratePlanViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.coach = User.objects.create_user("coach", password="x-Kairos-1234", role="coach")
        cls.other_coach = User.objects.create_user("other", password="x-Kairos-1234", role="coach")
        cls.client_user = User.objects.create_user("runner", password="x-Kairos-1234", role="client")
        cls.profile = ClientProfile.objects.create(user=cls.client_user, coach=cls.coach, experience="advanced",
                                                   runs_per_week=6, long_run_day="Sun", quality_day="Wed",
                                                   target_race_name="Spring Half", target_race_date=RACE_SAT)
        cls.url = reverse("generate_plan", args=[cls.profile.pk])

    def post_data(self, **overrides):
        data = {"plan_type": "half_marathon", "race_name": "Spring Half", "race_date": "2027-03-13", "weeks": "12",
                "experience": "intermediate", "current_mileage": "25", "longest_run": "8", "runs_per_week": "5",
                "long_run_day": "Sat", "quality_day": "Tue", "preferred_rest_days": ["Sun"]}
        data.update(overrides)
        return data

    def test_form_is_prefilled_from_the_profile(self):
        self.client.force_login(self.coach)
        form = self.client.get(self.url).context["form"]
        self.assertEqual(form.initial["experience"], "advanced")
        self.assertEqual(form.initial["long_run_day"], "Sun")
        self.assertEqual(form.initial["race_date"], RACE_SAT)

    def test_post_creates_a_hidden_draft_and_opens_it(self):
        self.client.force_login(self.coach)
        with mock.patch("training.views.client_today", return_value=TODAY):
            response = self.client.post(self.url, self.post_data())
        plan = TrainingPlan.objects.get()
        self.assertRedirects(response, reverse("plan_detail", args=[plan.pk]))
        self.assertEqual(plan.status, "draft")
        self.client.force_login(self.client_user)
        self.assertEqual(self.client.get(reverse("plan_detail", args=[plan.pk])).status_code, 404)

    def test_bad_input_shows_errors_and_saves_nothing(self):
        self.client.force_login(self.coach)
        with mock.patch("training.views.client_today", return_value=TODAY):
            response = self.client.post(self.url, self.post_data(weeks="25", quality_day="Sat"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertFalse(TrainingPlan.objects.exists())

    def test_race_too_soon_is_explained(self):
        self.client.force_login(self.coach)
        with mock.patch("training.views.client_today", return_value=TODAY):
            response = self.client.post(self.url, self.post_data(race_date="2026-12-19"))
        self.assertContains(response, "start in the past")
        self.assertFalse(TrainingPlan.objects.exists())

    def test_other_coach_and_clients_are_refused(self):
        self.client.force_login(self.other_coach)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.post(self.url, self.post_data()).status_code, 404)
        self.client.force_login(self.client_user)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertFalse(TrainingPlan.objects.exists())
