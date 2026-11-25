from django import template

from core.units import format_distance, format_duration

register = template.Library()


@register.filter
def distance(metres, units="mi"):
    return format_distance(metres, units)


@register.filter
def duration(seconds):
    return format_duration(seconds)


@register.filter
def add_days(day, n):
    from datetime import timedelta

    return day + timedelta(days=int(n)) if day else day


@register.filter
def undo_plan_id(tags):
    """Messages tagged "undo plan-<id>" get an Undo button (base.html)."""
    for tag in str(tags).split():
        if tag.startswith("plan-") and tag[5:].isdigit():
            return int(tag[5:])
    return None

