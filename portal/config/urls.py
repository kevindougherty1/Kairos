from django.contrib import admin
from django.urls import include, path

from core import views as core_views
from training import views as training_views

admin.site.site_header = "Hard Left Admin"
admin.site.site_title = "Hard Left Admin"
admin.site.index_title = "Coaching Data"

urlpatterns = [
    path("admin/", admin.site.urls),
    # login, logout, password_change, password_reset (templates in portal/templates/registration/)
    path("accounts/", include("django.contrib.auth.urls")),
    path("", core_views.home, name="home"),
    path("dashboard/", training_views.dashboard, name="dashboard"),
    path("coach/", training_views.coach_home, name="coach_home"),
    path("coach/clients/<int:client_id>/generate/", training_views.generate_plan, name="generate_plan"),
    path("me/", training_views.client_home, name="client_home"),
    path("plans/<int:pk>/", training_views.plan_detail, name="plan_detail"),
    path("workouts/<int:pk>/", training_views.workout_detail, name="workout_detail"),
]
