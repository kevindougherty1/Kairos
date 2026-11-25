from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ClientProfile, User


@admin.register(User)
class KairosUserAdmin(UserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "role", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff")
    fieldsets = UserAdmin.fieldsets + (("Coaching Role", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Coaching Role", {"fields": ("role",)}),)


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ("__str__", "coach", "experience", "target_race_name", "target_race_date", "preferred_units")
    list_filter = ("coach", "experience")
    search_fields = ("user__username", "user__first_name", "user__last_name", "target_race_name")
    autocomplete_fields = ("user", "coach")
    fieldsets = (
        (None, {"fields": ("user", "coach")}),
        ("Goals and Background", {"fields": ("goals", "training_background", "experience")}),
        ("Target Race", {"fields": ("target_race_name", "target_race_date", "target_race_distance_m")}),
        ("Schedule Preferences", {
            "fields": ("runs_per_week", "long_run_day", "quality_day", "unavailable_days", "preferred_rest_days"),
        }),
        ("Display", {"fields": ("timezone", "preferred_units")}),
    )
