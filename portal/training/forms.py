import re
from decimal import Decimal

from django import forms

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

    def __init__(self, *args, units="mi", **kwargs):
        super().__init__(*args, **kwargs)
        self.units = units
        self.fields["distance"].label = f"Distance ({units})"
        self.fields["perceived_effort"].widget.attrs.update(min=1, max=10)
        if self.instance.pk:
            per = METRES_PER_KM if units == "km" else METRES_PER_MILE
            if self.instance.actual_distance_m is not None:
                self.initial["distance"] = round(Decimal(self.instance.actual_distance_m) / Decimal(per), 2)
            if self.instance.actual_duration_s is not None:
                h, rem = divmod(self.instance.actual_duration_s, 3600)
                m, s = divmod(rem, 60)
                self.initial["duration"] = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

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
