import re
from decimal import Decimal

from django import forms

from accounts.models import Experience, Weekday
from core.units import METRES_PER_KM, METRES_PER_MILE
from .models import WorkoutResult

_DURATION = re.compile(r"^(?:(\d+):)?([0-5]?\d):([0-5]\d)$")


def parse_duration(text):
    """'45:00' or '1:05:30' -> seconds."""
    match = _DURATION.match(text.strip())
    if not match:
        raise forms.ValidationError("Use minutes:seconds (45:00) or hours:minutes:seconds (1:05:30).")
    hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
    return hours * 3600 + minutes * 60 + seconds


class GeneratePlanForm(forms.Form):
    """Coach-only. Field rules mirror engines.PlanRequest.validate (which runs again in the service)."""

    plan_type = forms.ChoiceField(
        label="Plan type",
        choices=[("half_marathon", "Half Marathon (8–20 weeks)")],
        help_text="Marathon generation comes next.",
    )
    race_name = forms.CharField(label="Race name", max_length=120, required=False)
    race_date = forms.DateField(label="Race date", widget=forms.DateInput(attrs={"type": "date"}))
    weeks = forms.IntegerField(label="Plan length (weeks)", min_value=8, max_value=20, initial=12)
    experience = forms.ChoiceField(label="Experience", choices=Experience.choices)
    current_mileage = forms.IntegerField(label="Current weekly miles", min_value=0, max_value=150)
    longest_run = forms.IntegerField(label="Longest recent run (mi)", min_value=0, max_value=40)
    runs_per_week = forms.TypedChoiceField(
        label="Runs per week", coerce=int, choices=[(n, str(n)) for n in (4, 5, 6)], initial=5
    )
    long_run_day = forms.ChoiceField(label="Long run day", choices=Weekday.choices, initial="Sat")
    quality_day = forms.ChoiceField(label="Workout day", choices=Weekday.choices, initial="Tue")
    unavailable_days = forms.MultipleChoiceField(
        label="Can't run on", choices=Weekday.choices, required=False, widget=forms.CheckboxSelectMultiple
    )
    preferred_rest_days = forms.MultipleChoiceField(
        label="Prefers to rest on", choices=Weekday.choices, required=False, widget=forms.CheckboxSelectMultiple
    )

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)
        for name in ("current_mileage", "longest_run", "weeks"):
            self.fields[name].widget.attrs["inputmode"] = "numeric"
        for f in self.fields.values():
            f.widget.attrs.setdefault("autocomplete", "off")

    @classmethod
    def initial_from(cls, profile):
        initial = {
            "experience": profile.experience or "intermediate",
            "runs_per_week": profile.runs_per_week if profile.runs_per_week in (4, 5, 6) else 5,
            "long_run_day": profile.long_run_day,
            "quality_day": profile.quality_day,
            "unavailable_days": profile.unavailable_days,
            "preferred_rest_days": profile.preferred_rest_days,
            "race_name": profile.target_race_name,
            "race_date": profile.target_race_date,
        }
        return {k: v for k, v in initial.items() if v not in (None, "")}

    def clean(self):
        data = super().clean()
        if data.get("long_run_day") and data.get("long_run_day") == data.get("quality_day"):
            self.add_error("quality_day", "Pick a different day from the long run.")
        return data

    def focus_first_error(self):
        for name in self.fields:
            if name in self.errors:
                self.fields[name].widget.attrs["autofocus"] = True
                break


class WorkoutResultForm(forms.ModelForm):
    """What a client may submit. Ownership, workout and prescription version are set by the view,
    never taken from the request (brief §6: no client-controlled ownership fields)."""

    distance = forms.DecimalField(
        required=False, min_value=Decimal("0"), max_value=Decimal("200"), decimal_places=2,
        label="Distance",
    )
    duration = forms.CharField(required=False, label="Time", help_text="e.g. 45:00 or 1:05:30")

    class Meta:
        model = WorkoutResult
        fields = ["status", "perceived_effort", "comments"]
        labels = {"perceived_effort": "Effort (1–10)"}
        widgets = {"comments": forms.Textarea(attrs={"rows": 4})}
        error_messages = {"status": {"required": "Choose how the run went: completed, partly done or skipped."}}

    def __init__(self, *args, units="mi", **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)
        self.units = units
        self.fields["distance"].label = f"Distance ({units})"
        self.fields["perceived_effort"].widget.attrs.update(min=1, max=10, inputmode="numeric")
        self.fields["distance"].widget.attrs.update(inputmode="decimal")
        for field in self.fields.values():  # not a login form: keep password managers out
            field.widget.attrs.setdefault("autocomplete", "off")
        if self.instance.pk:
            per = METRES_PER_KM if units == "km" else METRES_PER_MILE
            if self.instance.actual_distance_m is not None:
                self.initial["distance"] = (Decimal(self.instance.actual_distance_m) / Decimal(per)).quantize(Decimal("0.01")).normalize()
            if self.instance.actual_duration_s is not None:
                h, rem = divmod(self.instance.actual_duration_s, 3600)
                m, s = divmod(rem, 60)
                self.initial["duration"] = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

    def focus_first_error(self):
        """After a failed submit, put the cursor in the first field that needs fixing."""
        for name in self.fields:
            if name in self.errors:
                self.fields[name].widget.attrs["autofocus"] = True
                break

    def clean_duration(self):
        text = self.cleaned_data.get("duration", "")
        return parse_duration(text) if text.strip() else None

    def save(self, commit=True):
        result = super().save(commit=False)
        distance = self.cleaned_data.get("distance")
        per = METRES_PER_KM if self.units == "km" else METRES_PER_MILE
        result.actual_distance_m = round(float(distance) * per) if distance is not None else None
        result.actual_duration_s = self.cleaned_data.get("duration")
        if commit:
            result.save()
        return result


class PrescriptionForm(forms.Form):
    """Coach: what the client will see for this workout. The engine's suggestion is never copied in unless asked."""

    title = forms.CharField(label="Title", max_length=120, help_text="Clients see this, e.g. Speed Session.")
    distance = forms.DecimalField(label="Distance", required=False, min_value=Decimal("0"), max_value=Decimal("100"),
                                  decimal_places=2)
    prescription = forms.CharField(
        label="The workout", required=False, widget=forms.Textarea(attrs={"rows": 6}),
        help_text="What your client should do, e.g. 2 mi easy, 3 x 2 mi at threshold with 2 min jog, 1 mi easy.",
    )
    coach_notes = forms.CharField(label="Notes for your client", required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, units="mi", workout=None, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)
        self.units = units
        self.workout = workout
        self.fields["distance"].label = f"Distance ({units})"
        self.fields["distance"].widget.attrs["inputmode"] = "decimal"
        for f in self.fields.values():
            f.widget.attrs.setdefault("autocomplete", "off")

    @classmethod
    def initial_for(cls, workout, units="mi", use_suggestion=False):
        distance = cls.shown_distance(workout.target_distance_m, units)
        prescription = workout.prescription
        if use_suggestion and workout.suggestion and not prescription:
            prescription = workout.suggestion
        return {"title": workout.title, "distance": distance, "prescription": prescription,
                "coach_notes": workout.coach_notes}

    @staticmethod
    def shown_distance(metres, units):
        if metres is None:
            return None
        per = METRES_PER_KM if units == "km" else METRES_PER_MILE
        return (Decimal(metres) / Decimal(per)).quantize(Decimal("0.01")).normalize()

    def changes(self):
        d = self.cleaned_data
        per = METRES_PER_KM if self.units == "km" else METRES_PER_MILE
        distance = d.get("distance")
        if distance is None:
            metres = None
        elif self.workout is not None and self.shown_distance(self.workout.target_distance_m, self.units) == distance.normalize():
            metres = self.workout.target_distance_m  # untouched: keep the exact stored value (no rounding drift)
        else:
            metres = round(float(distance) * per)
        return {
            "title": d["title"].strip(),
            "target_distance_m": metres,
            "prescription": d["prescription"].strip(),
            "coach_notes": d["coach_notes"].strip(),
        }

    def focus_first_error(self):
        for name in self.fields:
            if name in self.errors:
                self.fields[name].widget.attrs["autofocus"] = True
                break
