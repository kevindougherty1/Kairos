from django.db import connection
from django.test import TestCase
from django.urls import reverse


class SkeletonTests(TestCase):
    def test_home_page_renders(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kairos Coaching")
        self.assertContains(response, reverse("login"))

    def test_admin_login_page_renders(self):
        response = self.client.get(reverse("admin:login"))
        self.assertEqual(response.status_code, 200)

    def test_database_is_postgres(self):
        self.assertEqual(connection.vendor, "postgresql")


class EngineImportTests(TestCase):
    """The portal imports the repo-root engines unchanged (portal/ENGINES.md)."""

    def test_marathon_engine_builds_a_plan(self):
        from engineV3 import build_plan

        prefs = {"long_run_day": "Sat", "speed_day": "Tue", "unavailable_days": [], "preferred_rest_days": ["Sun"]}
        plan = build_plan("intermediate", 30, 12, 5, 16, prefs)
        self.assertEqual(len(plan), 16)
        self.assertEqual(plan[-1]["phase"], "Race")

    def test_half_marathon_engine_builds_a_plan(self):
        from half_marathon_engine_main_4plus_v5_7 import build_plan

        peak, plan = build_plan("intermediate", 25, 8, 5, 12)
        self.assertEqual(len(plan), 12)
        self.assertEqual(plan[-1]["phase"], "Race")
        self.assertGreater(peak, 0)
